import { Card } from './index';

export function InsightCard({ title = 'Energy insight', text, children }) {
  return <Card title={title}><p>{text}</p>{children}</Card>;
}
