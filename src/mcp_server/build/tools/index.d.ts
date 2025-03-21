import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { NexusClient } from "../nexus-client.js";
import { Config } from "../config.js";
/**
 * Register all API tools with the MCP server
 */
export declare function registerTools(server: McpServer, nexusClient: NexusClient, config: Config): Promise<void>;
