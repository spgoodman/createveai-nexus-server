import { ICredentialDataDecryptedObject, IExecuteFunctions, IHookFunctions, ILoadOptionsFunctions, INodeListSearchResult, INodeProperties } from 'n8n-workflow';
import { IDataObject } from 'n8n-workflow';
/**
 * Fetch OpenAPI schema from the server
 */
export declare function fetchOpenApiSchema(this: ILoadOptionsFunctions | IExecuteFunctions | IHookFunctions, credentials: ICredentialDataDecryptedObject, force?: boolean): Promise<any>;
/**
 * Parse endpoints from OpenAPI schema
 */
export declare function parseEndpoints(schema: any): Array<{
    path: string;
    displayName: string;
    description?: string;
    isQueued?: boolean;
}>;
/**
 * Check if an endpoint uses queue mode
 */
export declare function isQueueEndpoint(schema: any, endpoint: string): boolean;
/**
 * Generate n8n fields based on OpenAPI schema
 */
export declare function generateFields(schema: any, endpoint: string): INodeProperties[];
/**
 * Build parameter object from values in n8n interface
 * Simplified for easier implementation
 */
export declare function buildRequestParameters(context: ILoadOptionsFunctions, itemIndex: number, endpoint: string): Promise<IDataObject>;
/**
 * Search for endpoints by name or description
 */
export declare function searchEndpoints(schema: any, query: string): INodeListSearchResult;
