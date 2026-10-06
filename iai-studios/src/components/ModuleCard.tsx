import { memo } from 'react'

interface ModuleCardProps {
  name: string
  hint: string
  index: number
  side: 'left' | 'right'
  onClick: () => void
}

export default memo(function ModuleCard({ name, hint, index, side, onClick }: ModuleCardProps) {
  return (
    <div onClick={onClick} className="mod-card-system transform-gpu">
      <div className={side === 'right' ? 'txt-r' : 'txt-l'}>
        <div className="mod-top-row">
          <span className="mod-id-tag">MOD.${String(index + 1).padStart(2, '0')}</span>
          <span className="mod-count-tag">{index < 6 ? index + 1 : index - 5}/06</span>
        </div>
        <h3 className="mod-title-text">{name}</h3>
        <p className="mod-hint-text">{hint}</p>
        <div className={`mod-visual-bar ${side === 'right' ? 'bar-r' : 'bar-l'}`} />
      </div>
    </div>
  )
})
