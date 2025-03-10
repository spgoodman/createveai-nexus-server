import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { NexusClient } from "../nexus-client.js";
import { Config } from "../config.js";
import { convertOpenApiToZodSchema } from "../utils/schema-converter.js";
import chalk from "chalk";

/**
 * Register all API tools with the MCP server
 */
export async function registerTools(
  server: McpServer,
  nexusClient: NexusClient,
  config: Config
): Promise<void> {
  try {
    console.error(chalk.blue("Fetching OpenAPI schema from Nexus server..."));
    
    // Fetch the OpenAPI schema to discover available APIs
    const openApiSchema = await nexusClient.getSchema();
    
    if (!openApiSchema.paths) {
      console.error(chalk.yellow("Warning: OpenAPI schema does not contain any paths"));
      return;
    }
    
    // Keep track of registered tools
    let registeredCount = 0;
    
    // Process each path in the schema
    for (const [path, pathItem] of Object.entries<any>(openApiSchema.paths)) {
      if (!path.startsWith('/api/')) continue;
      
      // Extract API path from URL path (remove /api/ prefix)
      const apiPath = path.substring(5);
      
      // Skip if API filter is set and doesn't match
      if (config.api && !apiPath.startsWith(config.api)) {
        continue;
      }
      
      // Get POST operation (we only handle POST requests)
      const postOp = pathItem.post;
      if (!postOp) continue;
      
      // Generate a tool name from API path
      const toolName = apiPath.replace(/\//g, '_');
      
      // Extract description and request body schema
      const description = postOp.summary || postOp.description || `API endpoint for ${apiPath}`;
      const requestBody = postOp.requestBody?.content?.['application/json']?.schema;
      
      if (!requestBody) {
        console.error(chalk.yellow(`Warning: No request schema found for ${apiPath}, skipping`));
        continue;
      }
      
      // Convert OpenAPI schema to Zod schema
      const schemaObj = convertOpenApiToZodSchema(requestBody);
      
      // Register the tool
      server.tool(
        toolName,
        schemaObj,
        // Tool implementation function
        async (params) => {
          try {
            // Execute the API call
            const result = await nexusClient.executeApi(apiPath, params);
            
            // Check if it's a queue operation
            if (result.queue_id) {
              return {
                content: [
                  {
                    type: "text",
                    text: `Operation queued with ID: ${result.queue_id}\n\nYou can check the status using the queue://${result.queue_id} resource.`
                  },
                  {
                    type: "json",
                    json: { queue_id: result.queue_id }
                  }
                ]
              };
            }
            
            // Format the response based on its structure
            return formatApiResponse(result);
          } catch (error: any) {
            // Return properly formatted error
            return {
              content: [
                {
                  type: "text",
                  text: `Error executing ${toolName}: ${error.message}`
                }
              ],
              isError: true
            };
          }
        },
        // Additional tool options
        {
          description
        }
      );
      
      registeredCount++;
      
      if (config.debug) {
        console.error(chalk.green(`Registered tool: ${toolName}`));
      }
    }
    
    console.error(chalk.green(`Successfully registered ${registeredCount} API tools`));
  } catch (error: any) {
    console.error(chalk.red(`Error registering tools: ${error.message}`));
  }
}

/**
 * Format API response in a way that's optimal for LLM consumption
 */
function formatApiResponse(result: any): { content: Array<{type: string, text?: string, json?: any}> } {
  const content: Array<{type: string, text?: string, json?: any}> = [];
  
  // Add text description if it makes sense
  if (result.message) {
    content.push({
      type: "text",
      text: result.message
    });
  }
  
  // Add the full JSON result
  content.push({
    type: "json",
    json: result
  });
  
  // Special handling for image results
  if (result.image_data) {
    content.push({
      type: "text",
      text: "Image generated successfully."
    });
  }
  
  return { content };
}
