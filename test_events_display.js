// Test script to verify event sections display across all languages
const fs = require('fs');
const path = require('path');

// Define language files to test
const languages = [
  { name: 'German', path: 'frontend/public/index.html' },
  { name: 'English', path: 'frontend/locales/en.html' },
  { name: 'Turkish', path: 'frontend/locales/tr.html' },
  { name: 'Russian', path: 'frontend/locales/ru.html' },
  { name: 'Arabic', path: 'frontend/locales/ar.html' },
  { name: 'Simple German', path: 'frontend/locales/einfach.html' }
];

// Elements to check for each language
const elementsToCheck = [
  { id: 'id="event1"', name: 'Event 1 Section' },
  { id: 'id="event2"', name: 'Event 2 Section' },
  { id: 'id="event3"', name: 'Event 3 Section' },
  { id: 'id="event4"', name: 'Event 4 Section' },
  { id: 'id="participants-modal-1"', name: 'Event 1 Modal' },
  { id: 'id="participants-modal-2"', name: 'Event 2 Modal' },
  { id: 'id="participants-modal-3"', name: 'Event 3 Modal' },
  { id: 'id="participants-modal-4"', name: 'Event 4 Modal' }
];

// Test results storage
const results = {};

// Run tests
function runTests() {
  console.log('=== Event Sections Display Test ===\n');

  for (const language of languages) {
    console.log(`Testing ${language.name} version...`);
    results[language.name] = { passed: 0, failed: 0, missing: [] };

    try {
      // Read the HTML file
      const filePath = path.resolve(language.path);
      const html = fs.readFileSync(filePath, 'utf8');

      // Test for each expected element using string matching
      for (const element of elementsToCheck) {
        if (html.includes(element.id)) {
          console.log(`✓ ${element.name} found`);
          results[language.name].passed++;
        } else {
          console.log(`✗ ${element.name} NOT found`);
          results[language.name].failed++;
          results[language.name].missing.push(element.name);
        }
      }

      console.log(`\nSummary for ${language.name}:`);
      console.log(`Passed: ${results[language.name].passed}`);
      console.log(`Failed: ${results[language.name].failed}`);

      if (results[language.name].missing.length > 0) {
        console.log(`Missing elements: ${results[language.name].missing.join(', ')}`);
      }
    } catch (error) {
      console.error(`Error testing ${language.name}: ${error.message}`);
    }

    console.log('\n----------------------\n');
  }

  // Overall summary
  console.log('=== Overall Test Results ===');
  let allPassed = true;

  for (const language in results) {
    const result = results[language];
    if (result.failed > 0) {
      allPassed = false;
      console.log(`${language}: ${result.passed}/${result.passed + result.failed} tests passed`);
    } else {
      console.log(`${language}: All tests passed`);
    }
  }

  if (allPassed) {
    console.log('\n✓✓✓ ALL LANGUAGES DISPLAY EVENT SECTIONS CORRECTLY ✓✓✓');
  } else {
    console.log('\n✗✗✗ SOME LANGUAGES HAVE MISSING EVENT SECTIONS ✗✗✗');
    console.log('\nLanguage switching might not work correctly due to path inconsistency:');
    console.log('1. frontend/locales/language_config.json uses: "file": "lang/[language].html"');
    console.log('2. HTML files use relative paths like: "[language].html" or "../index.html"');
  }
}

// Run the tests
runTests();