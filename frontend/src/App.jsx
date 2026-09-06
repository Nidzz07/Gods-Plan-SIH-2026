import { Route, Routes } from 'react-router-dom'

import Layout from './components/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Alerts from './pages/Alerts.jsx'
import CaseDetail from './pages/CaseDetail.jsx'
import District from './pages/District.jsx'
import Member from './pages/Member.jsx'
import Ministry from './pages/Ministry.jsx'
import NotFound from './pages/NotFound.jsx'
import Rulebook from './pages/Rulebook.jsx'
import SignIn from './pages/SignIn.jsx'
import StateNodal from './pages/StateNodal.jsx'
import DataGapReport from './pages/DataGapReport.jsx'
import SearchPage from './pages/SearchPage.jsx'
import StaticDocPage from './pages/StaticDocPage.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public Unauthenticated Landing Page (§6) */}
      <Route path="/" element={<Landing />} />

      {/* Authentication */}
      <Route path="/sign-in" element={<SignIn />} />

      {/* Public / Semi-public Documentation Routes */}
      <Route path="/reports/data-gap" element={<DataGapReport />} />
      <Route path="/docs/:docId" element={<StaticDocPage />} />
      <Route path="/audit/:caseId" element={<StaticDocPage />} />

      {/* Authenticated Dashboard Shell (§5 & §7) */}
      <Route element={<Layout />}>
        {/* Ministry National Overview */}
        <Route path="ministry" element={<Ministry />} />

        {/* State Overview & State comparison with parameter */}
        <Route path="state" element={<StateNodal />} />
        <Route path="state/:state" element={<StateNodal />} />

        {/* District Working Queue & District with state/district parameters */}
        <Route path="district" element={<District />} />
        <Route path="district/:state/:district" element={<District />} />

        {/* Member Account Overview */}
        <Route path="member" element={<Member />} />

        {/* Universal Case Sheet */}
        <Route path="cases/:caseId" element={<CaseDetail />} />

        {/* Rulebook & Alerts */}
        <Route path="rulebook" element={<Rulebook />} />
        <Route path="alerts" element={<Alerts />} />

        {/* Record Search */}
        <Route path="search" element={<SearchPage />} />

        {/* 404 handler */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
