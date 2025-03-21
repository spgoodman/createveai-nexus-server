import { z } from "zod";
import chalk from "chalk";
/**
 * Register all API tools with the MCP server
 */
export async function registerTools(server, nexusClient, config) {
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
        for (const [path, pathItem] of Object.entries(openApiSchema.paths)) {
            if (!path.startsWith('/api/'))
                continue;
            // Extract API path from URL path (remove /api/ prefix)
            const apiPath = path.substring(5);
            // Skip if API filter is set and doesn't match
            if (config.api && !apiPath.startsWith(config.api)) {
                continue;
            }
            // Get POST operation (we only handle POST requests)
            const postOp = pathItem.post;
            if (!postOp)
                continue;
            // Generate a tool name from API path
            const toolName = apiPath.replace(/\//g, '_');
            // Extract description and request body schema
            const description = postOp.summary || postOp.description || `API endpoint for ${apiPath}`;
            const requestBody = postOp.requestBody?.content?.['application/json']?.schema;
            if (!requestBody) {
                console.error(chalk.yellow(`Warning: No request schema found for ${apiPath}, skipping`));
                continue;
            }
            try {
                // Create a simple parameter schema with one 'data' parameter that accepts any JSON
                const toolParams = {
                    data: z.any().describe(`Input data for ${toolName}`)
                };
                // Register the tool with proper parameter order:
                // 1. name, 2. description (string), 3. params schema, 4. callback
                server.tool(toolName, description, toolParams, async (args, extra) => {
                    try {
                        // If data is not provided, use an empty object
                        const data = args.data || {};
                        // Execute the API call with the data field
                        const result = await nexusClient.executeApi(apiPath, data);
                        // Check if it's a queue operation
                        if (result.queue_id) {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Operation queued with ID: ${result.queue_id}\n\nYou can check the status using the queue://${result.queue_id} resource.`
                                    }
                                ]
                            };
                        }
                        // Format the response based on its structure
                        return formatApiResponse(result);
                    }
                    catch (error) {
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
                });
                registeredCount++;
                if (config.debug) {
                    console.error(chalk.green(`Registered tool: ${toolName}`));
                }
            }
            catch (error) {
                console.error(chalk.red(`Error registering tool ${toolName}: ${error.message}`));
            }
        }
        console.error(chalk.green(`Successfully registered ${registeredCount} API tools`));
    }
    catch (error) {
        console.error(chalk.red(`Error registering tools: ${error.message}`));
    }
}
/**
 * Format API response in a way that's optimal for LLM consumption
 */
function formatApiResponse(result) {
    const content = [];
    // Add text description if it makes sense
    if (result.message) {
        content.push({
            type: "text",
            text: result.message
        });
    }
    // Add the full JSON result as text
    content.push({
        type: "text",
        text: JSON.stringify(result, null, 2)
    });
    // Special handling for image results
    if (result.image_data) {
        content.push({
            type: "text",
            text: "Image generated successfully."
        });
        // If it's a base64 image, we could add it as an image type
        if (typeof result.image_data === "string" && result.image_data.startsWith("data:image/")) {
            try {
                const [header, data] = result.image_data.split(",");
                const mimeType = header.split(":")[1].split(";")[0];
                content.push({
                    type: "image",
                    data: data,
                    mimeType: mimeType
                });
            }
            catch (error) {
                console.error(chalk.yellow(`Failed to process image data: ${error}`));
            }
        }
    }
    return { content };
}
//# sourceMappingURL=index.js.map