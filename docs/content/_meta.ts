import type { MetaRecord } from 'nextra'

const meta: MetaRecord = {
  index: {
    type: 'page', 
    title: 'Home',
    display: "hidden" 
  },
  intro: {
    type: 'page',
    title: 'Introduction'
  },
  philosophy: {
    type: 'page',
    title: 'Philosophy'
  },
  stack: { 
    type: 'page', 
    title: 'Stack' 
  },
  docs: { 
    type: 'page', 
    title: 'Docs' 
  },
  api: { 
    type: 'page', 
    title: 'API'
  }
}

export default meta
