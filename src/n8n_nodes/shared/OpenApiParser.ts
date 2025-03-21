import {
	ICredentialDataDecryptedObject,
	IExecuteFunctions,
	IHookFunctions,
	ILoadOptionsFunctions,
	INodeListSearchResult,
	INodeProperties,
	INodePropertyOptions,
	NodeParameterValue,
} from 'n8n-workflow';
import { getApiClient } from './GenericFunctions';
import { IDataObject } from 'n8n-workflow';

/**
 * Cache for OpenAPI schemas to avoid refetching
 */
const schemaCache: Record<string, any> = {};

/**
 * Fetch OpenAPI schema from the server
 */
export async function fetchOpenApiSchema(
	this: ILoadOptionsFunctions | IExecuteFunctions | IHookFunctions,
	credentials: ICredentialDataDecryptedObject,
	force: boolean = false,
): Promise<any> {
	const apiUrl = credentials.apiUrl as string;
	const apiKey = credentials.apiKey as string;
	const schemaPath = credentials.schemaPath as string || '/openapi.json';
	
	// Generate cache key based on API URL and schema path
	const cacheKey = `${apiUrl}${schemaPath}`;
	
	// Return cached schema if available and not forcing refresh
	if (!force && schemaCache[cacheKey]) {
		return schemaCache[cacheKey];
	}
	
	// Create API client
	const client = getApiClient.call(this, apiUrl, apiKey);
	
	try {
		// Fetch OpenAPI schema
		const response = await client.get(schemaPath);
		
		// Cache the schema
		schemaCache[cacheKey] = response.data;
		
		return response.data;
	} catch (error) {
		// Clear cache on error
		delete schemaCache[cacheKey];
		throw error;
	}
}

/**
 * Parse endpoints from OpenAPI schema
 */
export function parseEndpoints(schema: any): Array<{
	path: string;
	displayName: string;
	description?: string;
	isQueued?: boolean;
}> {
	if (!schema.paths) {
		return [];
	}
	
	const endpoints: Array<{
		path: string;
		displayName: string;
		description?: string;
		isQueued?: boolean;
	}> = [];
	
	// Process each path
	for (const [path, pathItem] of Object.entries<any>(schema.paths)) {
		// Only process API endpoints
		if (!path.startsWith('/api/')) continue;
		
		// Get POST operation (we only handle POST requests)
		const postOp = pathItem.post;
		if (!postOp) continue;
		
		// Extract the path without the /api/ prefix
		const apiPath = path.substring(5);
		
		// Determine if endpoint is for queue status
		const isQueueEndpoint = apiPath.endsWith('/queue');
		if (isQueueEndpoint) continue; // Skip queue endpoints as they're handled internally
		
		// Format display name
		let displayName = apiPath.replace(/\//g, ' › ');
		if (postOp.summary) {
			displayName = postOp.summary;
		}
		
		// Get description
		const description = postOp.description || `API endpoint for ${apiPath}`;
		
		// Check if this is a queued endpoint - look for queue_id in responses
		let isQueued = false;
		if (postOp.responses) {
			for (const [_, response] of Object.entries<any>(postOp.responses)) {
				if (response.content?.['application/json']?.schema?.properties?.queue_id) {
					isQueued = true;
					break;
				}
			}
		}
		
		endpoints.push({
			path: apiPath,
			displayName,
			description,
			isQueued,
		});
	}
	
	return endpoints;
}

/**
 * Check if an endpoint uses queue mode
 */
export function isQueueEndpoint(schema: any, endpoint: string): boolean {
	if (!schema.paths) return false;
	
	// Get the full path with /api/ prefix
	const fullPath = `/api/${endpoint}`;
	const pathItem = schema.paths[fullPath];
	if (!pathItem || !pathItem.post) return false;
	
	// Check responses for queue_id
	const postOp = pathItem.post;
	if (postOp.responses) {
		for (const [_, response] of Object.entries<any>(postOp.responses)) {
			if (response.content?.['application/json']?.schema?.properties?.queue_id) {
				return true;
			}
		}
	}
	
	return false;
}

/**
 * Generate n8n fields based on OpenAPI schema
 */
export function generateFields(schema: any, endpoint: string): INodeProperties[] {
	if (!schema.paths) return [];
	
	// Get the full path with /api/ prefix
	const fullPath = `/api/${endpoint}`;
	const pathItem = schema.paths[fullPath];
	if (!pathItem || !pathItem.post) return [];
	
	const fields: INodeProperties[] = [];
	const postOp = pathItem.post;
	
	// Get parameters from the request body
	const requestBody = postOp.requestBody?.content?.['application/json']?.schema;
	if (requestBody) {
		// Process required parameters
		if (requestBody.properties) {
			const requiredParams = requestBody.required || [];
			
			for (const [propName, propSchema] of Object.entries<any>(requestBody.properties)) {
				const field = convertSchemaToField(
					propName,
					propSchema,
					requiredParams.includes(propName),
				);
				fields.push(field);
			}
		}
	}
	
	return fields;
}

/**
 * Build parameter object from values in n8n interface
 * Simplified for easier implementation
 */
export async function buildRequestParameters(
	context: ILoadOptionsFunctions,
	itemIndex: number,
	endpoint: string,
): Promise<IDataObject> {
	// Simplified implementation that just returns an empty object
	// In a real implementation, we would parse the OpenAPI schema and extract
	// the parameters based on the fields defined in it
	return {};
}

/**
 * Convert OpenAPI schema property to n8n field
 */
function convertSchemaToField(
	name: string,
	schema: any,
	required: boolean = false,
): INodeProperties {
	// Base field
	const field: INodeProperties = {
		displayName: formatDisplayName(name),
		name,
		type: 'string',
		default: schema.default,
		description: schema.description || `Parameter ${name}`,
		required,
	};
	
	// Type mapping
	switch (schema.type) {
		case 'string':
			// Handle special formats
			if (schema.format === 'binary' || schema.format === 'base64') {
				field.type = 'string';
				field.default = '={{ $binary }}';
				field.description = `${field.description} (Upload a file)`;
			} else if (schema.enum) {
				// Handle enum as options
				field.type = 'options';
				field.options = schema.enum.map((value: string) => ({
					name: value,
					value,
				}));
			} else if (schema.format === 'date-time') {
				field.type = 'dateTime';
			} else {
				// Regular string
				field.type = 'string';
				
				// Handle multiline
				if (schema.multiline === true) {
					field.typeOptions = {
						...(field.typeOptions || {}),
						rows: 4,
					};
				}
			}
			break;
			
		case 'number':
		case 'integer':
			field.type = 'number';
			
			// Add min/max
			if (schema.minimum !== undefined || schema.maximum !== undefined) {
				field.typeOptions = {
					...(field.typeOptions || {}),
					minValue: schema.minimum,
					maxValue: schema.maximum,
				};
			}
			break;
			
		case 'boolean':
			field.type = 'boolean';
			break;
			
		case 'array':
			// Handle arrays
			if (schema.items) {
				if (schema.items.type === 'string' && schema.items.enum) {
					// Array of enum values - use multi options
					field.type = 'multiOptions';
					field.options = schema.items.enum.map((value: string) => ({
						name: value,
						value,
					}));
				} else {
					// Generic array
					field.type = 'string';
					field.typeOptions = {
						...(field.typeOptions || {}),
						multipleValues: true,
					};
				}
			}
			break;
			
		case 'object':
			// Handle objects as JSON
			field.type = 'json';
			field.default = schema.default || '{}';
			break;
			
		default:
			// Default to string for unknown types
			field.type = 'string';
	}
	
	return field;
}

/**
 * Format property name as display name
 */
function formatDisplayName(name: string): string {
	return name
		.split('_')
		.map(word => word.charAt(0).toUpperCase() + word.slice(1))
		.join(' ');
}

/**
 * Search for endpoints by name or description
 */
export function searchEndpoints(
	schema: any,
	query: string,
): INodeListSearchResult {
	const endpoints = parseEndpoints(schema);
	const result: INodeListSearchResult = {
		results: [],
	};
	
	if (!query) {
		return {
			results: endpoints.map(endpoint => ({
				name: endpoint.displayName,
				value: endpoint.path,
				description: endpoint.description,
			})),
		};
	}
	
	// Lowercase query for case-insensitive search
	const lowerQuery = query.toLowerCase();
	
	// Filter endpoints
	for (const endpoint of endpoints) {
		if (
			endpoint.displayName.toLowerCase().includes(lowerQuery) ||
			endpoint.path.toLowerCase().includes(lowerQuery) ||
			(endpoint.description && endpoint.description.toLowerCase().includes(lowerQuery))
		) {
			result.results.push({
				name: endpoint.displayName,
				value: endpoint.path,
				description: endpoint.description,
			});
		}
	}
	
	return result;
}
