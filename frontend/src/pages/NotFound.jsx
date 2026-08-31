import { Link } from 'react-router-dom'

import PageHeader from '../components/PageHeader.jsx'
import { BUTTON, CARD } from '../ui.js'

// CLAUDE.md bans unstyled 404s. A wrong URL in front of judges should look
// like part of the product, not like a stack trace. It uses the same header
// band and content region as every other screen for exactly that reason.
export default function NotFound() {
  return (
    <article className="flex-1">
      <PageHeader
        title="No such screen"
        note="That route is not part of this build."
      />

      <div className="px-8 py-8">
        {/* Same CARD and BUTTON tokens as every other screen, rather than a
            hand-rolled border and a hand-rolled link. A 404 that styles itself
            is a 404 that drifts. */}
        <div className={`${CARD} min-h-region max-w-4xl p-8`}>
          <p className="text-body-secondary text-ink-secondary">
            Check the address, or start again from your own screen. Note that a case id outside
            your role&rsquo;s scope answers exactly like one that was never issued — the API will
            not confirm that another district&rsquo;s case exists, so a mistyped id and a real one
            you cannot reach look the same from here, deliberately.
          </p>
          {/* `/` is a redirect to whichever landing route this role owns, so
              one link works for all four without this page knowing which. */}
          <Link to="/" className={`${BUTTON} mt-4 inline-block`}>
            Back to your own screen
          </Link>
        </div>
      </div>
    </article>
  )
}
