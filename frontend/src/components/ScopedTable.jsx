import { useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'

import EmptyState from './EmptyState.jsx'
import SectionHeading from './SectionHeading.jsx'
import { CAPTION, CELL, CELL_NUM, COLUMN_HEAD, SORT_HEAD } from '../ui.js'

// The league table. One sortable table component for every dashboard that
// ranks a population it can name — the Ministry's states, a state's districts,
// a district's agencies.
//
// SCOPED, and the name is a claim about where that happens: every row this
// renders arrived from an endpoint that had already applied the caller's
// predicate. Nothing here filters, and nothing here may ever start to. A table
// that dropped rows in the browser would be the failure invariant 10 names,
// and it would pass a response-body test while doing it.
//
// SORTING IS THE ONE THING IT DOES BEYOND DISPLAY, and sorting is safe in a way
// filtering is not: it reorders rows the server already decided this caller may
// see. It is client-side because these are complete populations — 31 states, 74
// districts, one agency — not pages of a larger set. A paginated table sorted
// in the browser would sort only the page, which is the bug this note exists to
// stop someone reintroducing when a population outgrows a single response.
//
// The design system's tokens are applied HERE rather than by each caller, so a
// column definition carries what a column MEANS (its header, its accessor, and
// whether it is numeric) and never how it looks.

// A numeric column is right-aligned with tabular figures; a text column is
// neither. That is the whole of the styling decision, and it is made from one
// flag on the column definition rather than by each call site remembering to
// pass two classes.
function cellClass(column) {
  return column.columnDef.meta?.numeric ? CELL_NUM : CELL
}

// Alignment only — the header's type style is COLUMN_HEAD either way, and
// putting the alignment in one place stops the class list carrying `text-right`
// twice, which is how a later `text-left` override ends up losing to a
// duplicate of equal specificity.
function headAlign(column) {
  return column.columnDef.meta?.numeric ? 'text-right' : 'text-left'
}

export default function ScopedTable({
  title,
  caption,
  columns,
  data,
  initialSort,
  emptyTitle = 'No rows',
  emptyBody,
  footnote,
  // Returns a border-colour class for one row, or nothing. This is severity
  // pattern (1) — the coloured left-border on a full data row — and a table row
  // is a full data row, so the case queue carries its severity here.
  //
  // A row that takes an accent must NOT also carry a severity tag in one of its
  // cells: that is the same fact encoded twice, and `severity.js` is explicit
  // that where a row carries the border, its severity text is plain ink. The
  // accent is not a substitute for the label, though — a queue using this still
  // prints the severity word in a column, because colour is never the only
  // signal.
  rowAccent,
}) {
  const [sorting, setSorting] = useState(initialSort ?? [])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    // Descending first on a numeric column: every ranking in this product
    // answers "which is worst", and a first click that surfaced the smallest
    // count would be a click nobody wants.
    sortDescFirst: true,
  })

  return (
    <section>
      <SectionHeading title={title}>{caption}</SectionHeading>

      {data.length === 0 ? (
        <div className="mt-4">
          <EmptyState title={emptyTitle}>{emptyBody}</EmptyState>
        </div>
      ) : (
        <>
          {/* Wide tables scroll inside their own container rather than pushing
              the page sideways. A district table at eight columns overflows a
              laptop viewport, and a horizontally scrolling PAGE loses the
              sidebar. */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse">
              {/* Every table carries a one-line caption. It is the real <caption>
                  element rather than a paragraph above the table, so a screen
                  reader announces the table with its description attached. It is
                  visually hidden because SectionHeading has already printed the
                  same sentence in the page's own type — duplicating it below the
                  heading would print it twice on screen. */}
              <caption className="sr-only">{caption}</caption>

              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr
                    key={headerGroup.id}
                    // The header takes the same 4px transparent edge the rows
                    // take, so a column heading sits over its own column rather
                    // than 4px to the left of it.
                    className={`border-b border-border-strong bg-bg ${
                      rowAccent ? 'border-l-4 border-l-transparent' : ''
                    }`}
                  >
                    {headerGroup.headers.map((header) => {
                      const sortable = header.column.getCanSort()
                      const direction = header.column.getIsSorted()
                      return (
                        <th
                          key={header.id}
                          scope="col"
                          className={`${COLUMN_HEAD} ${headAlign(header.column)} px-4 pb-2`}
                          // The sort state, for a screen reader, on the element
                          // that carries it. A visual caret alone says nothing.
                          aria-sort={
                            direction === 'asc'
                              ? 'ascending'
                              : direction === 'desc'
                                ? 'descending'
                                : sortable
                                  ? 'none'
                                  : undefined
                          }
                        >
                          {sortable ? (
                            // A real button, so it is tabbable and picks up the
                            // global focus ring from index.css without this
                            // component defining one.
                            <button
                              type="button"
                              onClick={header.column.getToggleSortingHandler()}
                              // Exactly one colour class reaches this element:
                              // text-ink and text-ink-secondary are equal
                              // specificity and would resolve by stylesheet
                              // order, not by the order written here, so an
                              // active header would stay muted at random.
                              className={`${SORT_HEAD} ${
                                direction ? 'text-ink' : 'text-ink-secondary'
                              }`}
                            >
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext(),
                              )}
                              {/* A caret in text, not an icon dependency and
                                  not an emoji. Only on the sorted column: a
                                  neutral caret on every header is six pieces of
                                  furniture saying nothing. */}
                              {direction === 'asc' ? ' ↑' : direction === 'desc' ? ' ↓' : ''}
                            </button>
                          ) : (
                            flexRender(header.column.columnDef.header, header.getContext())
                          )}
                        </th>
                      )
                    })}
                  </tr>
                ))}
              </thead>

              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className={`border-b border-border last:border-b-0 ${
                      rowAccent
                        ? // border-l-4 only when an accent is actually returned:
                          // a 4px transparent edge on an unaccented row would
                          // shift its first cell out of line with the header.
                          `border-l-4 ${rowAccent(row.original) ?? 'border-l-transparent'}`
                        : ''
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className={`${cellClass(cell.column)} px-4 py-4`}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {footnote ? <p className={`${CAPTION} max-w-3xl`}>{footnote}</p> : null}
        </>
      )}
    </section>
  )
}
