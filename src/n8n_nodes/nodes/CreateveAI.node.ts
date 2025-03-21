import {
	IDataObject,
	IExecuteFunctions,
	ILoadOptionsFunctions,
	INodeExecutionData,
	INodePropertyOptions,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
	NodeConnectionType,
} from 'n8n-workflow';

import {
	executeApiRequest,
	pollQueueStatus,
} from '../shared/GenericFunctions';

import {
	fetchOpenApiSchema,
	generateFields,
	isQueueEndpoint,
	parseEndpoints,
} from '../shared/OpenApiParser';

import {
	handleBinaryInputData,
	processBinaryOutputData,
} from '../shared/BinaryDataHandlers';

export class CreateveAI implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Createve.AI',
		name: 'createveAI',
		icon: 'file:createveai.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["endpoint"]}}',
		description: 'Consume Createve.AI Nexus API endpoints dynamically',
		defaults: {
			name: 'Createve.AI',
			color: '#1976d2',
		},
		inputs: [{ type: NodeConnectionType.Main }],
		outputs: [{ type: NodeConnectionType.Main }],
		credentials: [
			{
				name: 'createveAIApi',
				required: true,
			},
		],
		properties: [
			// Endpoint selection
			{
				displayName: 'Endpoint',
				name: 'endpoint',
				type: 'options',
				noDataExpression: true,
				typeOptions: {
					loadOptionsMethod: 'getEndpoints',
				},
				default: '',
				description: 'API endpoint to call',
				required: true,
			},
			
			// Common parameter fields that might be used by API endpoints
			{
				displayName: 'Text',
				name: 'text',
				type: 'string',
				default: '',
				displayOptions: {
					show: {
						endpoint: ['text_processing/textAnalyzer', 'text_processing/textSummarizer'],
					},
				},
				description: 'Text to process',
			},
			
			{
				displayName: 'Summary Length',
				name: 'summary_length',
				type: 'number',
				default: 3,
				displayOptions: {
					show: {
						endpoint: ['text_processing/textSummarizer'],
					},
				},
				description: 'Number of sentences in the summary',
			},
			
			{
				displayName: 'Width',
				name: 'width',
				type: 'number',
				default: 512,
				displayOptions: {
					show: {
						endpoint: ['image_processing/imageResizer', 'image_processing/thumbnailGenerator'],
					},
				},
				description: 'Width of the output image',
			},
			
			{
				displayName: 'Height',
				name: 'height',
				type: 'number',
				default: 512,
				displayOptions: {
					show: {
						endpoint: ['image_processing/imageResizer', 'image_processing/thumbnailGenerator'],
					},
				},
				description: 'Height of the output image',
			},
			
			// Queue operations
			{
				displayName: 'Operation Mode',
				name: 'operationMode',
				type: 'options',
				options: [
					{
						name: 'Submit & Wait',
						value: 'submitAndWait',
						description: 'Submit job and wait for results',
					},
					{
						name: 'Submit Only',
						value: 'submitOnly',
						description: 'Submit job and return queue ID',
					},
					{
						name: 'Check Status',
						value: 'checkStatus',
						description: 'Check status of existing queue item',
					},
				],
				default: 'submitAndWait',
				description: 'How to handle queue-based operations',
			},
			
			{
				displayName: 'Queue ID',
				name: 'queueId',
				type: 'string',
				default: '',
				displayOptions: {
					show: {
						operationMode: ['checkStatus'],
					},
				},
				description: 'ID of the queue item to check',
				required: true,
			},
			
			{
				displayName: 'Max Poll Time (seconds)',
				name: 'maxPollTime',
				type: 'number',
				default: 300,
				displayOptions: {
					show: {
						operationMode: ['submitAndWait'],
					},
				},
				description: 'Maximum time to wait for results',
			},
			
			{
				displayName: 'Poll Interval (seconds)',
				name: 'pollInterval',
				type: 'number',
				default: 2,
				displayOptions: {
					show: {
						operationMode: ['submitAndWait'],
					},
				},
				description: 'Time between status checks',
			},
		],
	};

	methods = {
		loadOptions: {
			async getEndpoints(this: ILoadOptionsFunctions): Promise<INodePropertyOptions[]> {
				const credentials = await this.getCredentials('createveAIApi');
				
				if (!credentials) {
					throw new NodeOperationError(this.getNode(), 'No credentials provided');
				}
				
				try {
					const schema = await fetchOpenApiSchema.call(this, credentials);
					const endpoints = parseEndpoints(schema);
					
					return endpoints.map(endpoint => ({
						name: endpoint.displayName,
						value: endpoint.path,
						description: endpoint.description,
					}));
				} catch (error) {
					throw new NodeOperationError(
						this.getNode(),
						`Failed to load API endpoints: ${error.message}`,
					);
				}
			},
		},
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		// Get credentials
		const credentials = await this.getCredentials('createveAIApi');
		if (!credentials) {
			throw new NodeOperationError(this.getNode(), 'No credentials provided');
		}
		
		const apiUrl = credentials.apiUrl as string;
		const apiKey = credentials.apiKey as string;
		
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];
		
		for (let itemIndex = 0; itemIndex < items.length; itemIndex++) {
			try {
				// Get parameters
				const endpoint = this.getNodeParameter('endpoint', itemIndex) as string;
				const operationMode = this.getNodeParameter('operationMode', itemIndex) as string;
				
				// Handle queue status operation
				if (operationMode === 'checkStatus') {
					const queueId = this.getNodeParameter('queueId', itemIndex) as string;
					
					// Poll for result (just once)
					const result = await pollQueueStatus.call(
						this,
						apiUrl,
						apiKey,
						endpoint,
						queueId,
						1,
						1,
					);
					
					// Process binary data if present
					const returnItem = processBinaryOutputData(
						result,
						items[itemIndex],
						this.getExecutionId(),
					);
					
					returnData.push(returnItem);
					continue;
				}
				
				// Build parameters from node inputs
				const parameters: IDataObject = {};
				
				// Get endpoint-specific parameters
				if (endpoint === 'text_processing/textAnalyzer' || endpoint === 'text_processing/textSummarizer') {
					parameters.text = this.getNodeParameter('text', itemIndex) as string;
					
					if (endpoint === 'text_processing/textSummarizer') {
						parameters.summary_length = this.getNodeParameter('summary_length', itemIndex) as number;
					}
				} else if (endpoint === 'image_processing/imageResizer' || endpoint === 'image_processing/thumbnailGenerator') {
					parameters.width = this.getNodeParameter('width', itemIndex) as number;
					parameters.height = this.getNodeParameter('height', itemIndex) as number;
					
					// Get binary data for image
					handleBinaryInputData(parameters, items[itemIndex]);
				}
				
				// Execute the API request
				const response = await executeApiRequest.call(
					this,
					apiUrl,
					apiKey,
					endpoint,
					parameters,
				);
				
				// Check if response includes queue_id (indicating a queued operation)
				if (response.queue_id && operationMode === 'submitAndWait') {
					// Get polling settings
					const maxPollTime = this.getNodeParameter('maxPollTime', itemIndex, 300) as number;
					const pollInterval = this.getNodeParameter('pollInterval', itemIndex, 2) as number;
					
					// Poll for result
					const result = await pollQueueStatus.call(
						this,
						apiUrl,
						apiKey,
						endpoint,
						response.queue_id as string,
						maxPollTime,
						pollInterval,
					);
					
					// Process binary data if present
					const returnItem = processBinaryOutputData(
						result,
						items[itemIndex],
						this.getExecutionId(),
					);
					
					returnData.push(returnItem);
				} else {
					// Either direct response or queue ID only
					const returnItem = processBinaryOutputData(
						response,
						items[itemIndex],
						this.getExecutionId(),
					);
					
					returnData.push(returnItem);
				}
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: {
							error: error.message,
						},
					});
					continue;
				}
				throw error;
			}
		}
		
		return [returnData];
	}
}
