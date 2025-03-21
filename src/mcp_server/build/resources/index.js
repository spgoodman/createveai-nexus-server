import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import chalk from "chalk";
/**
 * Register all resources with the MCP server
 */
export async function registerResources(server, nexusClient, config) {
    try {
        console.error(chalk.blue("Setting up resources..."));
        // Register queue resources
        registerQueueResources(server, nexusClient);
        // Register documentation resources
        registerDocResources(server, nexusClient);
        // Register schema resources
        registerSchemaResources(server, nexusClient, config);
        console.error(chalk.green("Resources registered successfully"));
    }
    catch (error) {
        console.error(chalk.red(`Error registering resources: ${error.message}`));
    }
}
/**
 * Register queue-related resources
 */
function registerQueueResources(server, nexusClient) {
    // Register queue status resource template
    const queueTemplate = new ResourceTemplate("queue://{queueId}", { list: undefined });
    // Type-safe resource callback
    const queueHandler = async (uri, variables) => {
        try {
            const queueId = variables.queueId;
            const status = await nexusClient.getQueueStatus(queueId);
            return {
                contents: [{
                        uri: uri.href,
                        text: JSON.stringify(status, null, 2),
                        mimeType: "application/json"
                    }]
            };
        }
        catch (error) {
            return {
                contents: [{
                        uri: uri.href,
                        text: `Error fetching queue status: ${error.message}`,
                        mimeType: "text/plain"
                    }]
            };
        }
    };
    server.resource("queue", queueTemplate, queueHandler);
    console.error(chalk.green("Registered queue resources"));
}
/**
 * Register documentation resources
 */
function registerDocResources(server, nexusClient) {
    // Register main documentation resource
    server.resource("readme", "docs://readme", async (uri) => {
        try {
            const docs = await nexusClient.getDocumentation();
            return {
                contents: [{
                        uri: uri.href,
                        text: docs,
                        mimeType: "text/markdown"
                    }]
            };
        }
        catch (error) {
            return {
                contents: [{
                        uri: uri.href,
                        text: `Error fetching documentation: ${error.message}`,
                        mimeType: "text/plain"
                    }]
            };
        }
    });
    // Register documentation template for specific docs
    const docsTemplate = new ResourceTemplate("docs://{path}", { list: undefined });
    // Type-safe resource callback
    const docsHandler = async (uri, variables) => {
        try {
            const path = variables.path;
            const docs = await nexusClient.getDocumentation(path);
            // Determine MIME type based on path
            let mimeType = "text/plain";
            if (path.endsWith(".md")) {
                mimeType = "text/markdown";
            }
            else if (path.endsWith(".json")) {
                mimeType = "application/json";
            }
            return {
                contents: [{
                        uri: uri.href,
                        text: docs,
                        mimeType
                    }]
            };
        }
        catch (error) {
            return {
                contents: [{
                        uri: uri.href,
                        text: `Error fetching documentation: ${error.message}`,
                        mimeType: "text/plain"
                    }]
            };
        }
    };
    server.resource("docs", docsTemplate, docsHandler);
    console.error(chalk.green("Registered documentation resources"));
}
/**
 * Register schema resources
 */
function registerSchemaResources(server, nexusClient, config) {
    // Register OpenAPI schema resource
    server.resource("schema", "schema://openapi", async (uri) => {
        try {
            const schema = await nexusClient.getSchema();
            return {
                contents: [{
                        uri: uri.href,
                        text: JSON.stringify(schema, null, 2),
                        mimeType: "application/json"
                    }]
            };
        }
        catch (error) {
            return {
                contents: [{
                        uri: uri.href,
                        text: `Error fetching OpenAPI schema: ${error.message}`,
                        mimeType: "text/plain"
                    }]
            };
        }
    });
    // If there's an API filter, register a specific schema resource
    if (config.api) {
        // Register API-specific schema
        server.resource("api-schema", `schema://${config.api}`, async (uri) => {
            try {
                const schema = await nexusClient.getSchema();
                // Filter paths to only include those related to the specified API
                const filteredPaths = {};
                for (const [path, pathData] of Object.entries(schema.paths || {})) {
                    if (path.startsWith(`/api/${config.api}`)) {
                        filteredPaths[path] = pathData;
                    }
                }
                // Create a filtered schema
                const filteredSchema = {
                    ...schema,
                    paths: filteredPaths
                };
                return {
                    contents: [{
                            uri: uri.href,
                            text: JSON.stringify(filteredSchema, null, 2),
                            mimeType: "application/json"
                        }]
                };
            }
            catch (error) {
                return {
                    contents: [{
                            uri: uri.href,
                            text: `Error fetching OpenAPI schema: ${error.message}`,
                            mimeType: "text/plain"
                        }]
                };
            }
        });
    }
    console.error(chalk.green("Registered schema resources"));
}
//# sourceMappingURL=index.js.map