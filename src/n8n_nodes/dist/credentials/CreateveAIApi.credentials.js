"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CreateveAIApi = void 0;
class CreateveAIApi {
    constructor() {
        this.name = 'createveAIApi';
        this.displayName = 'Createve.AI API';
        this.documentationUrl = 'https://github.com/spgoodman/createveai-nexus-server/tree/master/src/n8n_nodes';
        this.properties = [
            {
                displayName: 'API URL',
                name: 'apiUrl',
                type: 'string',
                default: 'http://localhost:43080',
                description: 'URL of the Createve.AI API server',
                placeholder: 'https://nexus.example.com',
            },
            {
                displayName: 'API Key',
                name: 'apiKey',
                type: 'string',
                typeOptions: {
                    password: true,
                },
                default: '',
                description: 'API key for authentication with Bearer token',
                placeholder: 'sk-apiservertest1',
            },
            {
                displayName: 'OpenAPI Schema Path',
                name: 'schemaPath',
                type: 'string',
                default: '/openapi.json',
                description: 'Path to the OpenAPI schema',
            },
        ];
    }
}
exports.CreateveAIApi = CreateveAIApi;
//# sourceMappingURL=CreateveAIApi.credentials.js.map