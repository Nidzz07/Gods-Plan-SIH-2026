import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { AXIS_LINE, AXIS_TICK, GRID, INK, INK_SECONDARY, chartHeight } from '../chart.js'
import EmptyState from './EmptyState.jsx'
import SectionHeading from './SectionHeading.jsx'
import { CARD } from '../ui.js'

// One ranked horizontal bar chart, used by every dashboard that ranks a
// population — states by HIGH count, districts by severity mix, an agency's
// share of a district's case load.
//
// HORIZONTAL, AND THAT IS THE WHOLE REASON THIS SHAPE WAS CHOSEN. The category
// axis carries names — "Uttar Pradesh", "SHAHJAHANPUR", "DISTRICT MAGISTRATE
// JALAUN" — and a vertical bar chart has to either rotate those to 45 degrees
// or truncate them. Rotated axis labels are unreadable on a projector, and this
// is a screen that gets projected.
//
// It grows with its data rather than stretching to fill a fixed box, so a
// three-row chart and a ten-row chart have the same bar thickness and read as
// the same object.
//
// STACKING IS THE SAME COMPONENT. Passing one series draws a plain ranked bar;
// passing three draws them stacked, which is how the severity mix is shown. A
// second component for the stacked case would be two implementations of one
// chart that could drift apart.

// The tooltip is written out rather than styled through Recharts' props,
// because the default carries its own border radius and its own shadow — a
// second radius and a second depth, which the conventions allow exactly none
// of. This one is the CARD token, so it is the same surface as everything else.
function ChartTooltip({ active, payload, label, valueFormat }) {
  if (!active || !payload?.length) return null
  return (
    <div className={`${CARD} px-4 py-2`}>
      <p className="text-meta-label uppercase text-ink-secondary">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="num text-body-secondary text-ink">
          {/* The series name, always — the colour swatch is a second signal and
              never the only one. */}
          {entry.name}: {valueFormat ? valueFormat(entry.value) : entry.value}
        </p>
      ))}
    </div>
  )
}

export default function RankedBar({
  title,
  caption,
  data,
  categoryKey,
  series,
  valueFormat,
  axisLabel,
  categoryWidth = 160,
  emptyTitle = 'Nothing to rank',
  emptyBody,
}) {
  return (
    <section>
      <SectionHeading title={title}>{caption}</SectionHeading>

      {data.length === 0 ? (
        <div className="mt-4">
          <EmptyState title={emptyTitle}>{emptyBody}</EmptyState>
        </div>
      ) : (
        // bg-surface, not the bare page ground: the page carries a full-bleed
        // motif layer behind it, and a chart drawn straight onto that would
        // have the texture running between its grid lines.
        //
        // `num` so the axis ticks and the tooltip inherit tabular figures —
        // SVG text inherits font-variant-numeric, and a value axis whose digits
        // change width is an axis a reader cannot compare down.
        <div className={`${CARD} num mt-4 p-4`}>
          <ResponsiveContainer width="100%" height={chartHeight(data.length)}>
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 0, right: 16, bottom: axisLabel ? 24 : 8, left: 0 }}
              barCategoryGap="20%"
            >
              <CartesianGrid {...GRID} horizontal={false} />
              <XAxis
                type="number"
                tick={AXIS_TICK}
                axisLine={AXIS_LINE}
                tickLine={false}
                tickFormatter={valueFormat}
                // Units on the axis, never left to be inferred from the bars.
                label={
                  axisLabel
                    ? {
                        value: axisLabel,
                        position: 'insideBottom',
                        offset: -12,
                        fill: INK_SECONDARY,
                        fontSize: 12,
                      }
                    : undefined
                }
              />
              <YAxis
                type="category"
                dataKey={categoryKey}
                width={categoryWidth}
                tick={{ ...AXIS_TICK, fill: INK }}
                axisLine={false}
                tickLine={false}
                // EVERY category gets its label. Recharts thins category ticks
                // by default, and on a one-row chart it drops the only one —
                // which is how a district implemented by a single agency ended
                // up drawing one unlabelled bar. That is the exact case the
                // chart exists to describe, and an unlabelled bar describes
                // nothing. These charts are short by construction, so there is
                // no row count at which thinning would be wanted.
                interval={0}
              />
              <Tooltip
                content={<ChartTooltip valueFormat={valueFormat} />}
                // The default hover band is a grey fill with its own opacity.
                // surface-sunk is the ground this app already uses to mark a
                // row as receiving attention.
                cursor={{ fill: '#F3F0EA' }}
              />
              {series.map((entry) => (
                <Bar
                  key={entry.key}
                  dataKey={entry.key}
                  name={entry.label}
                  // Explicit on every bar. An omitted fill is how the banned
                  // default palette actually gets into a build.
                  fill={entry.color}
                  stackId={series.length > 1 ? 'severity' : undefined}
                  // No `radius` prop: a bar rounded on one end is a second
                  // radius token wearing a disguise, and there is one.
                  //
                  // Animation off. A bar that grows on mount is decoration that
                  // costs a demo the first second of every screen, and it
                  // replays on every re-render a filter causes.
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>

          {/* The legend is written in text rather than drawn by Recharts, whose
              default legend is a row of coloured dots — round, which is the
              rounded-full the conventions ban. Swatches are 8px squares at the
              app's one radius, and each carries its label. Only drawn when
              there is more than one series: a legend of one is noise. */}
          {series.length > 1 ? (
            <ul className="mt-4 flex flex-wrap gap-4">
              {series.map((entry) => (
                <li key={entry.key} className="flex items-center gap-1">
                  <span
                    className="inline-block h-2 w-2 rounded"
                    style={{ backgroundColor: entry.color }}
                    aria-hidden="true"
                  />
                  <span className="text-meta-label uppercase text-ink-secondary">
                    {entry.label}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      )}
    </section>
  )
}
