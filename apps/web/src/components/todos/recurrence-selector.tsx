'use client'

import { Repeat } from 'lucide-react'

interface RecurrenceData {
  type: string
  interval: number
  days: string
  endDate: string
}

interface RecurrenceSelectorProps {
  recurrenceType: string
  interval: number
  days: string
  endDate: string
  onChange: (data: RecurrenceData) => void
}

const WEEKDAYS = [
  { short: 'M', full: 'Monday', value: 'mon' },
  { short: 'T', full: 'Tuesday', value: 'tue' },
  { short: 'W', full: 'Wednesday', value: 'wed' },
  { short: 'T', full: 'Thursday', value: 'thu' },
  { short: 'F', full: 'Friday', value: 'fri' },
  { short: 'S', full: 'Saturday', value: 'sat' },
  { short: 'S', full: 'Sunday', value: 'sun' },
]

/**
 * Recurrence selector component for todo creation/editing.
 * Supports daily, weekly, monthly recurrence with interval and end date.
 */
export function RecurrenceSelector({
  recurrenceType,
  interval,
  days,
  endDate,
  onChange,
}: RecurrenceSelectorProps) {
  const selectedDays = days ? days.split(',') : []

  const toggleDay = (day: string) => {
    const newDays = selectedDays.includes(day)
      ? selectedDays.filter((d) => d !== day)
      : [...selectedDays, day]
    onChange({
      type: recurrenceType,
      interval,
      days: newDays.join(','),
      endDate,
    })
  }

  const handleTypeChange = (newType: string) => {
    onChange({
      type: newType,
      interval: newType === 'none' ? 1 : interval,
      days: newType === 'weekly' ? days : '',
      endDate: newType === 'none' ? '' : endDate,
    })
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Type selector */}
      <label className="flex items-center gap-1.5 text-xs text-muted">
        <Repeat size={12} />
        <select
          value={recurrenceType}
          onChange={(e) => handleTypeChange(e.target.value)}
          className="h-7 rounded border border-border bg-background px-2
            text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="none">No repeat</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
      </label>

      {recurrenceType !== 'none' && (
        <>
          {/* Interval input */}
          <label className="flex items-center gap-1.5 text-xs text-muted">
            <span>Every</span>
            <input
              type="number"
              min="1"
              max="99"
              value={interval}
              onChange={(e) => onChange({
                type: recurrenceType,
                interval: parseInt(e.target.value) || 1,
                days,
                endDate,
              })}
              className="h-7 w-16 rounded border border-border bg-background px-2
                text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <span>{recurrenceType}{interval > 1 ? 's' : ''}</span>
          </label>

          {/* Weekday checkboxes (only for weekly) */}
          {recurrenceType === 'weekly' && (
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <span>On:</span>
              <div className="flex gap-1">
                {WEEKDAYS.map((day, idx) => (
                  <button
                    key={day.value}
                    type="button"
                    onClick={() => toggleDay(day.value)}
                    className={`flex h-6 w-6 items-center justify-center rounded
                      border text-xs transition-colors
                      ${selectedDays.includes(day.value)
                        ? 'border-accent bg-accent text-black'
                        : 'border-border bg-background text-muted hover:border-foreground'
                      }`}
                    title={day.full}
                  >
                    {day.short}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* End date picker */}
          <label className="flex items-center gap-1.5 text-xs text-muted">
            <span>Until</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => onChange({
                type: recurrenceType,
                interval,
                days,
                endDate: e.target.value,
              })}
              className="h-7 rounded border border-border bg-background px-2
                text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <span className="text-[10px]">(optional)</span>
          </label>
        </>
      )}
    </div>
  )
}
