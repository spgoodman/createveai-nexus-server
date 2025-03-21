import { z } from "zod";
declare const ConfigSchema: z.ZodObject<{
    baseUrl: z.ZodString;
    apiKey: z.ZodString;
    api: z.ZodOptional<z.ZodString>;
    debug: z.ZodDefault<z.ZodBoolean>;
}, "strip", z.ZodTypeAny, {
    baseUrl: string;
    apiKey: string;
    debug: boolean;
    api?: string | undefined;
}, {
    baseUrl: string;
    apiKey: string;
    api?: string | undefined;
    debug?: boolean | undefined;
}>;
export type Config = z.infer<typeof ConfigSchema>;
export declare function loadConfig(): Config;
export {};
