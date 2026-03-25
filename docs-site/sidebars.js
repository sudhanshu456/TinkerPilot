// @ts-check

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.

 @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  // But you can create a sidebar manually
  tutorialSidebar: [
    'index',
    'architecture',
    {
      type: 'category',
      label: 'Getting Started',
      items: ['getting-started/setup', 'getting-started/running-the-app'],
    },
    {
      type: 'category',
      label: 'Implementation',
      items: [
        'implementation/backend',
        'implementation/frontend',
        'implementation/local-ai',
      ],
    },
    'project-structure',
    'cli-reference',
    'how-to-extend',
  ],
};

export default sidebars;
