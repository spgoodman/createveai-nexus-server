import {
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

export class CreateveAIApi implements ICredentialType {
	name = 'createveAIApi';
	displayName = 'Createve.AI API';
	documentationUrl = 'https://github.com/spgoodman/createveai-nexus-server/tree/master/src/n8n_nodes';
	properties: INodeProperties[] = [
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
