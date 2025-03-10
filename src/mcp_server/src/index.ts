#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import chalk from "chalk";
import { loadConfig } from "./config.js";
import { NexusClient } from "./nexus-client.js";
import { registerTools } from "./tools/index.js";
import { registerResources } from "./resources/index.js";

/**
 * Createve.AI Nexus MCP Server
 * 
 * This MCP server connects to a remote Createve.AI Nexus server via its REST API
 * and exposes its functionality through the Model Context Protocol.
 */
async function main() {
  console.error(chalk.blue("Starting Createve.AI Nexus MCP Server..."));
  
  try {
    // Load configuration
    const config = loadConfig();
    
    // Show configuration
    console.error(chalk.blue("Configuration:"));
    console.error(chalk.blue(`- Base URL: ${config.baseUrl}`));
    console.error(chalk.blue(`- API Filter: ${config.api || 'None (all APIs exposed)'}`));
    console.error(chalk.blue(`- Debug Mode: ${config.debug ? 'Enabled' : 'Disabled'}`));
    
    // Create MCP server
    const server = new McpServer({
      name: "createveai-nexus-mcp",
      version: "1.0.0",
      description: "MCP interface for Createve.AI Nexus Server"
    });
    
    // Create Nexus REST client
    const nexusClient = new NexusClient(config);
    
    // Register tools and resources
    await registerTools(server, nexusClient, config);
    await registerResources(server, nexusClient, config);
    
    // Connect to stdio transport
    console.error(chalk.green("Connecting to stdio transport..."));
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    console.error(chalk.green("Createve.AI Nexus MCP Server running"));
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.error(chalk.yellow("\nShutting down..."));
      process.exit(0);
    });
  } catch (error: any) {
    console.error(chalk.red(`Error starting MCP server: ${error.message}`));
    if (error.stack && process.env.DEBUG) {
      console.error(chalk.red(error.stack));
    }
    process.exit(1);
  }
}

// Start the server
main().catch(error => {
  console.error(chalk.red("Unhandled error:"));
  console.error(chalk.red(error));
  process.exit(1);
});
