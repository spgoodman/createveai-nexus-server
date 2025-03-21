"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.searchEndpoints = exports.buildRequestParameters = exports.generateFields = exports.isQueueEndpoint = exports.parseEndpoints = exports.fetchOpenApiSchema = void 0;
const GenericFunctions_1 = require("./GenericFunctions");
/**
 * Cache for OpenAPI schemas to avoid refetching
 */
const schemaCache = {};
/**
 * Fetch OpenAPI schema from the server
 */
async function fetchOpenApiSchema(credentials, force = false) {
    const apiUrl = credentials.apiUrl;
    const apiKey = credentials.apiKey;
    const schemaPath = credentials.schemaPath || '/openapi.json';
    // Generate cache key based on API URL and schema path
    const cacheKey = `${apiUrl}${schemaPath}`;
    // Return cached schema if available and not forcing refresh
    if (!force && schemaCache[cacheKey]) {
        return schemaCache[cacheKey];
    }
    // Create API client
    const client = GenericFunctions_1.getApiClient.call(this, apiUrl, apiKey);
    try {
        // Fetch OpenAPI schema
        const response = await client.get(schemaPath);
        // Cache the schema
        schemaCache[cacheKey] = response.data;
        return response.data;
    }
    catch (error) {
        // Clear cache on error
        delete schemaCache[cacheKey];
        throw error;
    }
}
exports.fetchOpenApiSchema = fetchOpenApiSchema;
/**
 * Parse endpoints from OpenAPI schema
 */
function parseEndpoints(schema) {
    var _a, _b, _c, _d;
    if (!schema.paths) {
        return [];
    }
    const endpoints = [];
    // Process each path
    for (const [path, pathItem] of Object.entries(schema.paths)) {
        // Only process API endpoints
        if (!path.startsWith('/api/'))
            continue;
        // Get POST operation (we only handle POST requests)
        const postOp = pathItem.post;
        if (!postOp)
            continue;
        // Extract the path without the /api/ prefix
        const apiPath = path.substring(5);
        // Determine if endpoint is for queue status
        const isQueueEndpoint = apiPath.endsWith('/queue');
        if (isQueueEndpoint)
            continue; // Skip queue endpoints as they're handled internally
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
            for (const [_, response] of Object.entries(postOp.responses)) {
                if ((_d = (_c = (_b = (_a = response.content) === null || _a === void 0 ? void 0 : _a['application/json']) === null || _b === void 0 ? void 0 : _b.schema) === null || _c === void 0 ? void 0 : _c.properties) === null || _d === void 0 ? void 0 : _d.queue_id) {
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
exports.parseEndpoints = parseEndpoints;
/**
 * Check if an endpoint uses queue mode
 */
function isQueueEndpoint(schema, endpoint) {
    var _a, _b, _c, _d;
    if (!schema.paths)
        return false;
    // Get the full path with /api/ prefix
    const fullPath = `/api/${endpoint}`;
    const pathItem = schema.paths[fullPath];
    if (!pathItem || !pathItem.post)
        return false;
    // Check responses for queue_id
    const postOp = pathItem.post;
    if (postOp.responses) {
        for (const [_, response] of Object.entries(postOp.responses)) {
            if ((_d = (_c = (_b = (_a = response.content) === null || _a === void 0 ? void 0 : _a['application/json']) === null || _b === void 0 ? void 0 : _b.schema) === null || _c === void 0 ? void 0 : _c.properties) === null || _d === void 0 ? void 0 : _d.queue_id) {
                return true;
            }
        }
    }
    return false;
}
exports.isQueueEndpoint = isQueueEndpoint;
/**
 * Generate n8n fields based on OpenAPI schema
 */
function generateFields(schema, endpoint) {
    var _a, _b, _c;
    if (!schema.paths)
        return [];
    // Get the full path with /api/ prefix
    const fullPath = `/api/${endpoint}`;
    const pathItem = schema.paths[fullPath];
    if (!pathItem || !pathItem.post)
        return [];
    const fields = [];
    const postOp = pathItem.post;
    // Get parameters from the request body
    const requestBody = (_c = (_b = (_a = postOp.requestBody) === null || _a === void 0 ? void 0 : _a.content) === null || _b === void 0 ? void 0 : _b['application/json']) === null || _c === void 0 ? void 0 : _c.schema;
    if (requestBody) {
        // Process required parameters
        if (requestBody.properties) {
            const requiredParams = requestBody.required || [];
            for (const [propName, propSchema] of Object.entries(requestBody.properties)) {
                const field = convertSchemaToField(propName, propSchema, requiredParams.includes(propName));
                fields.push(field);
            }
        }
    }
    return fields;
}
exports.generateFields = generateFields;
/**
 * Build parameter object from values in n8n interface
 * Simplified for easier implementation
 */
async function buildRequestParameters(context, itemIndex, endpoint) {
    // Simplified implementation that just returns an empty object
    // In a real implementation, we would parse the OpenAPI schema and extract
    // the parameters based on the fields defined in it
    return {};
}
exports.buildRequestParameters = buildRequestParameters;
/**
 * Convert OpenAPI schema property to n8n field
 */
function convertSchemaToField(name, schema, required = false) {
    // Base field
    const field = {
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
            }
            else if (schema.enum) {
                // Handle enum as options
                field.type = 'options';
                field.options = schema.enum.map((value) => ({
                    name: value,
                    value,
                }));
            }
            else if (schema.format === 'date-time') {
                field.type = 'dateTime';
            }
            else {
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
                    field.options = schema.items.enum.map((value) => ({
                        name: value,
                        value,
                    }));
                }
                else {
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
function formatDisplayName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
/**
 * Search for endpoints by name or description
 */
function searchEndpoints(schema, query) {
    const endpoints = parseEndpoints(schema);
    const result = {
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
        if (endpoint.displayName.toLowerCase().includes(lowerQuery) ||
            endpoint.path.toLowerCase().includes(lowerQuery) ||
            (endpoint.description && endpoint.description.toLowerCase().includes(lowerQuery))) {
            result.results.push({
                name: endpoint.displayName,
                value: endpoint.path,
                description: endpoint.description,
            });
        }
    }
    return result;
}
exports.searchEndpoints = searchEndpoints;
//# sourceMappingURL=OpenApiParser.js.map