// A simple test to verify the n8n node package was built correctly
const { nodeTypes, credentialTypes } = require('./dist/index');

console.log('Node Types:');
console.log(Object.keys(nodeTypes));

console.log('\nCredential Types:');
console.log(Object.keys(credentialTypes));

// Check if the main classes are available
if (nodeTypes.CreateveAI && credentialTypes.CreateveAIApi) {
  console.log('\nTest PASSED: Main classes are properly exported');
} else {
  console.error('\nTest FAILED: One or more required classes are missing');
  process.exit(1);
}

console.log('\nPackage is ready to be published!');
