import { motion } from 'framer-motion'

export function GeneralLayout({ content }: { content: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="font-body text-sm text-kip-charcoal leading-relaxed max-w-2xl bg-white border border-kip-light rounded-2xl rounded-tl-sm px-4 py-3 shadow-card">
      <p className="whitespace-pre-wrap">{content}</p>
    </motion.div>
  )
}

import BusinessIdeaLayout from './BusinessIdeaLayout'
import CrisisLayout from './CrisisLayout'
import RegulatoryLayout from './RegulatoryLayout'
import EconomicLayout from './EconomicLayout'
import { ResponseType, BusinessIdeaData, CrisisData, RegulatoryData, EconomicData } from '@/types'

interface RouterProps {
  responseType:    ResponseType
  content:         string
  structured:      any | null
  onStartJourney?: () => void
}

export function ResponseRouter({ responseType, content, structured, onStartJourney }: RouterProps) {
  if (responseType === 'business_idea'     && structured) return <BusinessIdeaLayout data={structured as BusinessIdeaData} onStartJourney={onStartJourney} />
  if (responseType === 'crisis'             && structured) return <CrisisLayout data={structured as CrisisData} />
  if (responseType === 'regulatory'         && structured) return <RegulatoryLayout data={structured as RegulatoryData} />
  if (responseType === 'economic_analysis'  && structured) return <EconomicLayout data={structured as EconomicData} />
  return <GeneralLayout content={content} />
}
