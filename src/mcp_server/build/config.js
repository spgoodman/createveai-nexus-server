import { z } from "zod";
import dotenv from "dotenv";
import chalk from "chalk";
// Load environment variables from .env file if present
dotenv.config();
// Configuration schema
const ConfigSchema = z.object({
    baseUrl: z.string().url("Base URL must be a valid URL"),
    apiKey: z.string().min(1, "API key is required"),
    api: z.string().optional(),
    debug: z.boolean().default(false),
});
export function loadConfig() {
    // Parse command line args
    const args = parseCommandLineArgs();
    // Build config object from environment variables and command line args
    // Command line args take precedence over environment variables
    const config = {
        baseUrl: args.baseUrl || process.env.CREATEVEAI_NEXUS_BASE_URL || "",
        apiKey: args.apiKey || process.env.CREATEVEAI_NEXUS_API_KEY || "",
        api: args.api || process.env.CREATEVEAI_NEXUS_API,
        debug: args.debug !== undefined ?
            args.debug :
            process.env.DEBUG?.includes("createveai-nexus-mcp") || false,
    };
    // Validate config
    try {
        return ConfigSchema.parse(config);
    }
    catch (error) {
        if (error instanceof z.ZodError) {
            console.error(chalk.red("Configuration Error:"));
            error.errors.forEach(err => {
                console.error(chalk.red(`- ${err.path.join(".")}: ${err.message}`));
            });
            console.error("");
            console.error(chalk.yellow("Please provide the required configuration via environment variables:"));
            console.error(chalk.yellow("  CREATEVEAI_NEXUS_BASE_URL=https://nexus.createve.ai"));
            console.error(chalk.yellow("  CREATEVEAI_NEXUS_API_KEY=your-api-key"));
            console.error("");
            console.error(chalk.yellow("Or via command line arguments:"));
            console.error(chalk.yellow("  --base-url https://nexus.createve.ai --api-key your-api-key"));
        }
        else {
            console.error(chalk.red("Unexpected error:"), error);
        }
        process.exit(1);
    }
}
function parseCommandLineArgs() {
    const args = process.argv.slice(2);
    const result = {};
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case "--base-url":
                if (i + 1 < args.length) {
                    result.baseUrl = args[i + 1];
                    i++;
                }
                break;
            case "--api-key":
                if (i + 1 < args.length) {
                    result.apiKey = args[i + 1];
                    i++;
                }
                break;
            case "--api":
                if (i + 1 < args.length) {
                    result.api = args[i + 1];
                    i++;
                }
                break;
            case "--debug":
                result.debug = true;
                break;
        }
    }
    return result;
}
//# sourceMappingURL=config.js.map