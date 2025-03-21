import { z } from "zod";
/**
 * Converts an OpenAPI schema object to a Zod schema
 * This is a simplified implementation that handles common types
 */
export declare function convertOpenApiToZodSchema(openApiSchema: any): Record<string, z.ZodTypeAny>;
