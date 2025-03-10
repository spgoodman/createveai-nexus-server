import { z } from "zod";

/**
 * Converts an OpenAPI schema object to a Zod schema
 * This is a simplified implementation that handles common types
 */
export function convertOpenApiToZodSchema(openApiSchema: any): Record<string, z.ZodTypeAny> {
  const result: Record<string, z.ZodTypeAny> = {};
  
  if (!openApiSchema.properties) {
    return result;
  }
  
  // Process each property in the schema
  for (const [propName, propSchema] of Object.entries<any>(openApiSchema.properties)) {
    let zodSchema: z.ZodTypeAny;
    
    // Basic type conversion
    switch (propSchema.type) {
      case "string":
        zodSchema = z.string();
        
        // Add string format validations
        if (propSchema.format === "email") {
          zodSchema = z.string().email();
        } else if (propSchema.format === "uri" || propSchema.format === "url") {
          zodSchema = z.string().url();
        } else if (propSchema.format === "uuid") {
          zodSchema = z.string().uuid();
        }
        
        // Add string length validations
        if (propSchema.minLength !== undefined) {
          zodSchema = z.string().min(propSchema.minLength);
        }
        if (propSchema.maxLength !== undefined) {
          zodSchema = z.string().max(propSchema.maxLength);
        }
        
        // Add pattern validation
        if (propSchema.pattern) {
          zodSchema = z.string().regex(new RegExp(propSchema.pattern));
        }
        
        // Add enum validation
        if (propSchema.enum) {
          zodSchema = z.enum(propSchema.enum);
        }
        break;
        
      case "number":
      case "integer":
        zodSchema = propSchema.type === "integer" ? z.number().int() : z.number();
        
        // Add numeric validations
        if (propSchema.minimum !== undefined) {
          zodSchema = z.number().min(propSchema.minimum);
        }
        if (propSchema.maximum !== undefined) {
          zodSchema = z.number().max(propSchema.maximum);
        }
        if (propSchema.multipleOf !== undefined) {
          zodSchema = z.number().multipleOf(propSchema.multipleOf);
        }
        break;
        
      case "boolean":
        zodSchema = z.boolean();
        break;
        
      case "array":
        // Handle arrays with nested items
        let itemSchema: z.ZodTypeAny = z.any();
        
        if (propSchema.items) {
          const convertedItems = convertOpenApiToZodSchema({ properties: { item: propSchema.items } });
          itemSchema = convertedItems.item;
        }
        
        zodSchema = z.array(itemSchema);
        
        // Add array validations
        if (propSchema.minItems !== undefined) {
          zodSchema = z.array(itemSchema).min(propSchema.minItems);
        }
        if (propSchema.maxItems !== undefined) {
          zodSchema = z.array(itemSchema).max(propSchema.maxItems);
        }
        break;
        
      case "object":
        // Handle nested objects recursively
        if (propSchema.properties) {
          const nestedSchema = convertOpenApiToZodSchema(propSchema);
          zodSchema = z.object(nestedSchema);
        } else {
          zodSchema = z.record(z.any());
        }
        break;
        
      default:
        // For any unhandled type, use z.any()
        zodSchema = z.any();
    }
    
    // Add description if available
    if (propSchema.description) {
      zodSchema = zodSchema.describe(propSchema.description);
    }
    
    // Handle nullable properties
    if (propSchema.nullable === true) {
      zodSchema = zodSchema.nullable();
    }
    
    // Add default value if specified
    if (propSchema.default !== undefined) {
      zodSchema = zodSchema.default(propSchema.default);
    }
    
    // Make required or optional based on the required array
    const isRequired = openApiSchema.required && openApiSchema.required.includes(propName);
    result[propName] = isRequired ? zodSchema : zodSchema.optional();
  }
  
  return result;
}
