import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { NexusClient } from "../nexus-client.js";
import { Config } from "../config.js";
/**
 * Register all resources with the MCP server
 */
export declare function registerResources(server: McpServer, nexusClient: NexusClient, config: Config): Promise<void>;
