'use client'

import { useState, useEffect } from 'react'
import TournamentFixtureTable from '../components/TournamentFixtureTable'
import TournamentStandingsTable from '../components/TournamentStandingsTable'

// Utility function to convert 24-hour format to 12-hour format with AM/PM
function formatTimeTo12Hour(time24: string): string {
  if (!time24) return 'N/A';
  
  // Handle both "HH:MM:SS" and "HH:MM" formats
  const [hours, minutes] = time24.split(':');
  const hour24 = parseInt(hours, 10);
  
  if (hour24 === 0) {
    return `12:${minutes} AM`;
  } else if (hour24 < 12) {
    return `${hour24}:${minutes} AM`;
  } else if (hour24 === 12) {
    return `12:${minutes} PM`;
  } else {
    return `${hour24 - 12}:${minutes} PM`;
  }
}

interface Tournament {
  id: string
  name: string
  sport_type: string
  max_teams: number
  start_date: string
  end_date: string
}

interface Team {
  id: string
  name: string
  captain_name: string
  tournament_id: string
}

interface Match {
  id: string
  team1_id: string
  team2_id: string
  court_id: string
  time_slot_id: string
  scheduled_date: string
  scheduled_time: string
  status: string
  tournament_id: string
}

interface Schedule {
  id: string
  tournament_id: string
  week_start_date: string
  week_end_date: string
  status: string
}

interface Court {
  id: string
  name: string
  location?: string
}

interface TimeSlot {
  id: string
  day_of_week: string
  start_time: string
  end_time: string
}

interface TeamRestriction {
  id: string
  team_id: string
  restriction_date: string
  restriction_type: string
  restriction_value?: string
  notes?: string
}

export default function DashboardPage() {
  const [tournaments, setTournaments] = useState<Tournament[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [matches, setMatches] = useState<Match[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [courts, setCourts] = useState<Court[]>([])
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([])
  const [teamRestrictions, setTeamRestrictions] = useState<TeamRestriction[]>([])
  const [selectedTournament, setSelectedTournament] = useState('')
  const [loading, setLoading] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [lastSaturdayDate, setLastSaturdayDate] = useState<string | null | undefined>(undefined)
  const [showRestrictions, setShowRestrictions] = useState(false)
  const [showAddRestriction, setShowAddRestriction] = useState(false)
  const [editingRestriction, setEditingRestriction] = useState<TeamRestriction | null>(null)
  const [selectedTeamForRestriction, setSelectedTeamForRestriction] = useState('')
  const [restrictionType, setRestrictionType] = useState('not_scheduled')
  const [restrictionValue, setRestrictionValue] = useState('')
  const [restrictionNotes, setRestrictionNotes] = useState('')
  const [restrictionDate, setRestrictionDate] = useState('')
  const [tournamentFixtures, setTournamentFixtures] = useState<any>(null)
  const [fixtureUpdateTimestamp, setFixtureUpdateTimestamp] = useState<number>(Date.now())
  const [activeTab, setActiveTab] = useState<'fixtures' | 'standings'>('fixtures')
  const [selectedTournamentForFixtures, setSelectedTournamentForFixtures] = useState('')

  const nextSaturday = '2025-09-06' // Hardcoded for now to match backend

  // Fetch data
  const fetchData = async () => {
    try {
      // Fetch tournaments
      const tournamentsRes = await fetch('http://localhost:8000/tournaments')
      if (tournamentsRes.ok) {
        const data = await tournamentsRes.json()
        setTournaments(data.tournaments || [])
      }

      // Fetch teams
      const teamsRes = await fetch('http://localhost:8000/teams')
      if (teamsRes.ok) {
        const data = await teamsRes.json()
        setTeams(data.teams || [])
      }

      // Fetch matches
      const matchesRes = await fetch('http://localhost:8000/matches')
      if (matchesRes.ok) {
        const data = await matchesRes.json()
        setMatches(data.matches || [])
      }

      // Fetch courts
      const courtsRes = await fetch('http://localhost:8000/courts')
      if (courtsRes.ok) {
        const data = await courtsRes.json()
        setCourts(Array.isArray(data) ? data : [])
      }

      // Fetch schedules
      const schedulesRes = await fetch('http://localhost:8000/schedules')
      if (schedulesRes.ok) {
        const data = await schedulesRes.json()
        setSchedules(data.schedules || [])
      }

      // Fetch time slots
      const timeSlotsRes = await fetch('http://localhost:8000/time-slots')
      if (timeSlotsRes.ok) {
        const data = await timeSlotsRes.json()
        setTimeSlots(Array.isArray(data) ? data : [])
      }

      // Fetch restrictions
      const restrictionsRes = await fetch('http://localhost:8000/team-restrictions')
      if (restrictionsRes.ok) {
        const data = await restrictionsRes.json()
        setTeamRestrictions(data.restrictions || [])
      }

    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])


  // Fetch tournament fixtures
  const fetchTournamentFixtures = async (tournamentId: string) => {
    if (!tournamentId) return
    
    try {
      const response = await fetch(`http://localhost:8000/tournaments/${tournamentId}/fixtures`)
      if (response.ok) {
        const data = await response.json()
        setTournamentFixtures(data.fixtures || [])
      } else {
        console.error('Failed to fetch fixtures:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error fetching tournament fixtures:', error)
    }
  }

  // Handle tournament change for fixtures
  const handleTournamentChange = (tournamentId: string) => {
    setSelectedTournamentForFixtures(tournamentId)
    setFixtureUpdateTimestamp(Date.now())
    fetchTournamentFixtures(tournamentId)
    setActiveTab('fixtures')
  }

  // Generate tournament fixtures
  const handleGenerateFixtures = async (forceRegenerate = false) => {
    if (!selectedTournamentForFixtures) {
      alert('Por favor selecciona un torneo')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/tournaments/${selectedTournamentForFixtures}/generate-fixtures?preserve_scores=${!forceRegenerate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const result = await response.json()
        if (result.warning === 'existing_scores' && !forceRegenerate) {
          const confirmed = window.confirm(
            `⚠️ ADVERTENCIA: Este torneo ya tiene resultados guardados.\n\n¿Estás seguro de que quieres regenerar la estructura? Esto eliminará todos los resultados existentes.\n\nPresiona "Aceptar" para continuar o "Cancelar" para preservar los resultados.`
          )
          if (confirmed) {
            await handleGenerateFixtures(true)
          }
        } else {
          alert(result.message)
          setFixtureUpdateTimestamp(Date.now())
          fetchTournamentFixtures(selectedTournamentForFixtures)
        }
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail}`)
      }
    } catch (error) {
      alert(`Error: ${error}`)
    }
  }

  // Handle fixture result update
  const handleFixtureResultUpdate = async (fixtureId: string, team1Score: number, team2Score: number) => {
    try {
      const response = await fetch(`http://localhost:8000/fixtures/${fixtureId}/result?team1_score=${team1Score}&team2_score=${team2Score}&updated_by=Organizador`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        setFixtureUpdateTimestamp(Date.now())
        fetchTournamentFixtures(selectedTournamentForFixtures)
      } else {
        const error = await response.json()
        alert(`Error al guardar los cambios: ${error.detail}`)
      }
    } catch (error) {
      alert(`Error al guardar los cambios: ${error}`)
    }
  }

  // Create Saturday schedule
  const createSaturdaySchedule = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/scheduler/saturday?request_date=${nextSaturday}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const result = await response.json()
        const matchesCount = result.total_matches || result.matches_scheduled || result.matches || 0
        alert(`Saturday schedule created successfully! ${matchesCount} matches scheduled across all tournaments.`)
        setLastSaturdayDate(nextSaturday)
        // Force refresh of all data
        await fetchData()
        // Force a re-render by updating a dummy state
        setFixtureUpdateTimestamp(Date.now())
      } else {
        const error = await response.json()
        alert(`Failed to create Saturday schedule: ${JSON.stringify(error.detail)}`)
      }
    } catch (error) {
      alert(`Error creating Saturday schedule: ${error}`)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch team restrictions
  const fetchTeamRestrictions = async () => {
    try {
      const restrictionsRes = await fetch('http://localhost:8000/team-restrictions')
      if (restrictionsRes.ok) {
        const data = await restrictionsRes.json()
        setTeamRestrictions(data.restrictions || [])
      }
    } catch (error) {
      console.error('Error fetching restrictions:', error)
    }
  }

  // Check if team already has a restriction for the selected date
  const checkExistingRestriction = (teamId: string, restrictionDate: string) => {
    return teamRestrictions.some(restriction => 
      restriction.team_id === teamId && 
      restriction.restriction_date === restrictionDate &&
      (!editingRestriction || restriction.id !== editingRestriction.id)
    )
  }

  // Handle team restriction save
  const handleSaveRestriction = async () => {
    if (!selectedTeamForRestriction || !restrictionType || !restrictionDate) {
      alert('Por favor completa todos los campos requeridos')
      return
    }

    // Check for duplicate restriction (only for new restrictions, not when editing)
    if (!editingRestriction && checkExistingRestriction(selectedTeamForRestriction, restrictionDate)) {
      const team = teams.find(t => t.id === selectedTeamForRestriction)
      const tournament = tournaments.find(t => t.id === team?.tournament_id)
      alert(`⚠️ Este equipo ya tiene una restricción para la fecha ${restrictionDate}.\n\nEquipo: ${team?.name || 'Unknown'} (${tournament?.name || 'Sin torneo'})\n\nPor favor selecciona otra fecha o edita la restricción existente.`)
      return
    }

    try {
      const restrictionData = {
        team_id: selectedTeamForRestriction,
        restriction_date: restrictionDate,
        restriction_type: restrictionType,
        restriction_value: restrictionValue || null,
        notes: restrictionNotes || null
      }

      console.log('Saving restriction:', restrictionData)

      let response
      if (editingRestriction) {
        // Update existing restriction
        response = await fetch(`http://localhost:8000/team-restrictions/${editingRestriction.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(restrictionData),
        })
      } else {
        // Create new restriction
        response = await fetch('http://localhost:8000/team-restrictions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(restrictionData),
        })
      }

      if (response.ok) {
        alert(editingRestriction ? 'Restricción actualizada exitosamente' : 'Restricción guardada exitosamente')
        setShowAddRestriction(false)
        setEditingRestriction(null)
        setSelectedTeamForRestriction('')
        setRestrictionType('not_scheduled')
        setRestrictionValue('')
        setRestrictionNotes('')
        setRestrictionDate('')
        // Refresh only the restrictions list
        fetchTeamRestrictions()
      } else {
        const error = await response.json()
        alert(`Error al guardar la restricción: ${error.detail}`)
      }
    } catch (error) {
      alert(`Error al guardar la restricción: ${error}`)
    }
  }

  // Handle edit restriction
  const handleEditRestriction = (restriction: TeamRestriction) => {
    setEditingRestriction(restriction)
    setSelectedTeamForRestriction(restriction.team_id)
    setRestrictionType(restriction.restriction_type)
    setRestrictionValue(restriction.restriction_value || '')
    setRestrictionNotes(restriction.notes || '')
    setRestrictionDate(restriction.restriction_date)
    setShowAddRestriction(true)
    
    // Scroll to the form after a short delay to ensure it's rendered
    setTimeout(() => {
      const formElement = document.getElementById('restriction-form')
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  }

  // Handle delete restriction
  const handleDeleteRestriction = async (restrictionId: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta restricción?')) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/team-restrictions/${restrictionId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        alert('Restricción eliminada exitosamente')
        fetchTeamRestrictions()
      } else {
        const error = await response.json()
        alert(`Error al eliminar la restricción: ${error.detail}`)
      }
    } catch (error) {
      alert(`Error al eliminar la restricción: ${error}`)
    }
  }

  const getCourtName = (courtId: string): string => {
    const court = courts.find(c => c.id === courtId)
    return court ? court.name : `Court ${courtId}`
  }

  // Filter data
  const tournamentsWithTeams = (tournaments || []).filter(tournament => 
    (teams || []).some(team => team.tournament_id === tournament.id)
  )

  // Always show the most recent Saturday schedule
  const saturdayDateToShow = (() => {
    // First, check if we have a specific lastSaturdayDate set
    if (lastSaturdayDate !== undefined) {
      return lastSaturdayDate
    }
    
    // Then, check if we have matches for nextSaturday
    if ((matches || []).some(match => match.scheduled_date === nextSaturday)) {
      return nextSaturday
    }
    
    // Finally, find the most recent Saturday with matches
    const saturdayMatches = (matches || []).filter(match => {
      // Parse date as local date to avoid timezone issues
      const [year, month, day] = match.scheduled_date.split('-').map(Number)
      const matchDate = new Date(year, month - 1, day) // month is 0-indexed
      return matchDate.getDay() === 6 // Saturday
    })
    
    if (saturdayMatches.length > 0) {
      // Sort by date and get the most recent
      saturdayMatches.sort((a, b) => new Date(b.scheduled_date).getTime() - new Date(a.scheduled_date).getTime())
      return saturdayMatches[0].scheduled_date
    }
    
    return null
  })()

  const saturdayMatches = (matches || []).filter(match => 
    saturdayDateToShow && match.scheduled_date === saturdayDateToShow
  )

  // Calculate unscheduled teams for Saturday
  const scheduledTeamIds = new Set<string>()
  saturdayMatches.forEach(match => {
    scheduledTeamIds.add(match.team1_id)
    scheduledTeamIds.add(match.team2_id)
  })

  const unscheduledTeams = (teams || []).filter(team => 
    !scheduledTeamIds.has(team.id)
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando datos...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Panel de Control Sportify</h1>
          <p className="mt-2 text-gray-600">Gestión de torneos y programación automática</p>
            </div>

        {/* Tournament Management Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Gestión de Torneos</h2>
          
          <div className="flex flex-wrap gap-4 mb-6">
            <button
              onClick={createSaturdaySchedule}
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading ? 'Creando...' : 'Horario Sábado'}
            </button>
            
            <button 
              onClick={() => setShowRestrictions(!showRestrictions)}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              Restricciones Equipos
            </button>
            
          </div>

          {/* Management Summary Table */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Resumen de Gestión</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-200">
                    <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-900">Categoría</th>
                    <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-900">Cantidad</th>
                    <th className="border border-gray-300 px-4 py-2 text-left text-sm font-semibold text-gray-900">Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Torneos</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">{tournamentsWithTeams.length}</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Torneos activos en el sistema</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Equipos</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">{teams.length}</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Equipos registrados en todos los torneos</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Partidos Sábado</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">{saturdayMatches.length}</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Partidos programados para el próximo sábado</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Canchas</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">{courts.length}</td>
                    <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">Canchas disponibles para los partidos</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Team Restrictions Section */}
        {showRestrictions && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Restricciones de Equipos</h2>
              <button
                onClick={() => setShowAddRestriction(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Agregar Restricción
              </button>
            </div>

            {showAddRestriction && (
              <div id="restriction-form" className={`rounded-lg p-4 mb-4 transition-all duration-300 ${editingRestriction ? 'bg-blue-50 border-2 border-blue-200 shadow-lg' : 'bg-gray-50'}`}>
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
                  {editingRestriction && <span className="text-blue-600">✏️</span>}
                  <span>{editingRestriction ? 'Editar Restricción' : 'Nueva Restricción'}</span>
                  {editingRestriction && <span className="text-sm text-blue-600 bg-blue-100 px-2 py-1 rounded-full">Modo Edición</span>}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
          <select 
                      value={selectedTeamForRestriction}
                      onChange={(e) => setSelectedTeamForRestriction(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    >
                      <option value="">Seleccionar equipo</option>
                      {teams.map(team => {
                        const tournament = tournaments.find(t => t.id === team.tournament_id)
                        const hasRestriction = teamRestrictions.some(r => 
                          r.team_id === team.id && 
                          r.restriction_date === restrictionDate &&
                          (!editingRestriction || r.id !== editingRestriction.id)
                        )
                        return (
                          <option 
                            key={team.id} 
                            value={team.id}
                            disabled={hasRestriction}
                            className={hasRestriction ? 'text-gray-400' : ''}
                          >
                            {hasRestriction ? '⚠️ ' : ''}{team.name} ({tournament?.name || 'Sin torneo'})
                            {hasRestriction ? ' - Ya tiene restricción' : ''}
              </option>
                        )
                      })}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      ⚠️ Los equipos que ya tienen restricción para esta fecha aparecen deshabilitados
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
                    <input
                      type="date"
                      value={restrictionDate}
                      onChange={(e) => setRestrictionDate(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Restricción</label>
                    <select
                      value={restrictionType}
                      onChange={(e) => setRestrictionType(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    >
                      <option value="not_scheduled">No programar</option>
                      <option value="time_preference">Preferencia de hora específica</option>
                      <option value="time_after">Solo después de hora específica</option>
                      <option value="time_before">Solo antes de hora específica</option>
                      <option value="time_range">Rango de horas específico</option>
                      <option value="court_preference">Preferencia de cancha</option>
                      <option value="tournament_time_preference">Preferencia de torneo y hora</option>
          </select>
        </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {restrictionType === 'time_preference' ? 'Hora específica (ej: 15:00)' :
                       restrictionType === 'time_after' ? 'Solo después de esta hora (ej: 16:00)' :
                       restrictionType === 'time_before' ? 'Solo antes de esta hora (ej: 18:00)' :
                       restrictionType === 'time_range' ? 'Rango de horas (ej: 15:00-17:00)' :
                       restrictionType === 'court_preference' ? 'Cancha preferida (ej: Cancha Santa Helenita)' :
                       restrictionType === 'tournament_time_preference' ? 'Hora preferida (ej: 15:00)' :
                       'Valor de la restricción'}
                    </label>
                    <input
                      type="text"
                      value={restrictionValue}
                      onChange={(e) => setRestrictionValue(e.target.value)}
                      placeholder={
                        restrictionType === 'time_preference' ? 'Ej: 15:00 (hora exacta)' :
                        restrictionType === 'time_after' ? 'Ej: 16:00 (solo después de las 16:00)' :
                        restrictionType === 'time_before' ? 'Ej: 18:00 (solo antes de las 18:00)' :
                        restrictionType === 'time_range' ? 'Ej: 15:00-17:00 (entre las 15:00 y 17:00)' :
                        restrictionType === 'court_preference' ? 'Ej: Cancha Santa Helenita, Cancha La Clarita' :
                        restrictionType === 'tournament_time_preference' ? 'Ej: 15:00, 16:00, 17:00' :
                        'Valor de la restricción'
                      }
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
                    <textarea
                      value={restrictionNotes}
                      onChange={(e) => setRestrictionNotes(e.target.value)}
                      placeholder="Notas adicionales..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      rows={3}
                    />
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={handleSaveRestriction}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    {editingRestriction ? 'Actualizar' : 'Guardar'}
                  </button>
                  <button
                    onClick={() => {
                      setShowAddRestriction(false)
                      setEditingRestriction(null)
                      setSelectedTeamForRestriction('')
                      setRestrictionType('not_scheduled')
                      setRestrictionValue('')
                      setRestrictionNotes('')
                      setRestrictionDate('')
                    }}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {/* Group restrictions by tournament */}
            {tournaments.map(tournament => {
              const tournamentRestrictions = teamRestrictions.filter(restriction => {
                const team = teams.find(t => t.id === restriction.team_id)
                return team?.tournament_id === tournament.id
              })

              if (tournamentRestrictions.length === 0) return null

              return (
                <div key={tournament.id} className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                      <span className="text-2xl">🏆</span>
                      <span>{tournament.name}</span>
                    </h3>
                    <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                      {tournamentRestrictions.length} restricción{tournamentRestrictions.length !== 1 ? 'es' : ''}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tournamentRestrictions.map(restriction => {
                const team = teams.find(t => t.id === restriction.team_id)
                const tournament = tournaments.find(t => t.id === team?.tournament_id)
                
                // Parse restriction value for better display
                let displayValue = ''
                let restrictionIcon = ''
                let restrictionColor = ''
                
                try {
                  const parsedValue = restriction.restriction_value ? JSON.parse(restriction.restriction_value) : {}
                  
                  switch (restriction.restriction_type) {
                    case 'not_scheduled':
                      displayValue = 'No programar'
                      restrictionIcon = '❌'
                      restrictionColor = 'bg-red-50 border-red-200'
                      break
                    case 'time_preference':
                      if (parsedValue.earliest_time) {
                        displayValue = `Solo después de ${parsedValue.earliest_time}`
                      } else if (parsedValue.preferred_times) {
                        displayValue = `Horas: ${parsedValue.preferred_times.join(', ')}`
                      } else {
                        displayValue = 'Preferencia de hora'
                      }
                      restrictionIcon = '⏰'
                      restrictionColor = 'bg-blue-50 border-blue-200'
                      break
                    case 'time_after':
                      displayValue = `Solo después de ${restriction.restriction_value}`
                      restrictionIcon = '⏰'
                      restrictionColor = 'bg-blue-50 border-blue-200'
                      break
                    case 'time_before':
                      displayValue = `Solo antes de ${restriction.restriction_value}`
                      restrictionIcon = '⏰'
                      restrictionColor = 'bg-blue-50 border-blue-200'
                      break
                    case 'time_range':
                      displayValue = `Entre ${restriction.restriction_value}`
                      restrictionIcon = '📅'
                      restrictionColor = 'bg-blue-50 border-blue-200'
                      break
                    case 'court_preference':
                      if (parsedValue.preferred_court) {
                        displayValue = `Cancha: ${parsedValue.preferred_court}`
                      } else {
                        displayValue = 'Preferencia de cancha'
                      }
                      restrictionIcon = '🏟️'
                      restrictionColor = 'bg-green-50 border-green-200'
                      break
                    case 'tournament_time_preference':
                      let timeText = ''
                      let courtText = ''
                      if (parsedValue.earliest_time) {
                        timeText = `después de ${parsedValue.earliest_time}`
                      }
                      if (parsedValue.preferred_court) {
                        courtText = `en ${parsedValue.preferred_court}`
                      }
                      displayValue = `${timeText} ${courtText}`.trim()
                      restrictionIcon = '🏆'
                      restrictionColor = 'bg-purple-50 border-purple-200'
                      break
                    default:
                      displayValue = restriction.restriction_value || 'Sin especificar'
                      restrictionIcon = 'ℹ️'
                      restrictionColor = 'bg-gray-50 border-gray-200'
                  }
                } catch (e) {
                  displayValue = restriction.restriction_value || 'Sin especificar'
                  restrictionIcon = 'ℹ️'
                  restrictionColor = 'bg-gray-50 border-gray-200'
                }
                
                                      return (
                        <div key={restriction.id} className={`p-4 rounded-lg border ${restrictionColor} relative group hover:shadow-sm transition-all duration-200`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className="text-lg">{restrictionIcon}</span>
                              <div>
                                <h4 className="font-semibold text-gray-900">{team?.name || 'Unknown'}</h4>
                                <p className="text-sm text-gray-600">{displayValue}</p>
              </div>
            </div>
                            <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => handleEditRestriction(restriction)}
                                className="flex items-center space-x-1 px-2 py-1 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                                title="Editar restricción"
                              >
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span>Editar</span>
                              </button>
                              <button
                                onClick={() => handleDeleteRestriction(restriction.id)}
                                className="flex items-center space-x-1 px-2 py-1 text-xs text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                                title="Eliminar restricción"
                              >
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                <span>Eliminar</span>
                              </button>
                            </div>
          </div>

                          {restriction.notes && (
                            <div className="mt-2 text-xs text-gray-500 italic">
                              "{restriction.notes}"
              </div>
                          )}
              </div>
                      )
                    })}
            </div>
          </div>
              )
            })}
            
            {/* Show message if no restrictions exist */}
            {teamRestrictions.length === 0 && (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">📋</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No hay restricciones</h3>
                <p className="text-gray-500">Agrega restricciones para equipos específicos usando el botón "Agregar Restricción"</p>
              </div>
            )}
              </div>
        )}

        {/* Tournament Fixtures Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Fixtures de Torneos</h2>
            
            {/* Tournament Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Seleccionar Torneo</label>
              <select
                value={selectedTournamentForFixtures}
                onChange={(e) => handleTournamentChange(e.target.value)}
                className="w-full max-w-md border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="">Seleccionar un torneo...</option>
                {tournamentsWithTeams.map(tournament => (
                  <option key={tournament.id} value={tournament.id}>{tournament.name}</option>
                ))}
              </select>
          </div>

            {selectedTournamentForFixtures && (
              <div className="mb-6">
                <button
                  onClick={() => handleGenerateFixtures()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Generar Estructura
                </button>
              </div>
            )}

            {selectedTournamentForFixtures && (
              <div className="mb-6">
                {tournamentFixtures && tournamentFixtures.length > 0 ? (
                  <>
                    <div className="flex space-x-1 mb-4">
                      <button
                        onClick={() => setActiveTab('fixtures')}
                        className={`px-4 py-2 rounded-lg ${
                          activeTab === 'fixtures'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        Fixtures
                      </button>
                      <button
                        onClick={() => setActiveTab('standings')}
                        className={`px-4 py-2 rounded-lg ${
                          activeTab === 'standings'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        Tabla de Posiciones
                      </button>
                    </div>

                    {activeTab === 'fixtures' && (
                      <TournamentFixtureTable
                        key={`${selectedTournamentForFixtures}-${fixtureUpdateTimestamp}`}
                        fixtures={tournamentFixtures}
                        tournamentId={selectedTournamentForFixtures}
                        teams={teams.filter(team => team.tournament_id === selectedTournamentForFixtures)}
                        onResultUpdate={handleFixtureResultUpdate}
                      />
                    )}

                    {activeTab === 'standings' && (
                      <TournamentStandingsTable
                        key={`${selectedTournamentForFixtures}-${fixtureUpdateTimestamp}`}
                        fixtures={tournamentFixtures}
                        tournamentId={selectedTournamentForFixtures}
                        teams={teams.filter(team => team.tournament_id === selectedTournamentForFixtures)}
                      />
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-4xl mb-4">🏆</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No hay fixtures generados</h3>
                    <p className="text-gray-500 mb-4">Haz clic en "Generar Estructura" para crear los fixtures del torneo</p>
                  </div>
                )}
              </div>
            )}
          </div>

        {/* Saturday Schedule Section */}
        {saturdayDateToShow ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Horario de Torneos del Sábado</h2>
            <p className="text-gray-600 mb-6">Fecha: {saturdayDateToShow}</p>
            
            {saturdayMatches.length > 0 ? (
              <div className="space-y-6">
                {/* Court Schedule Tables */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Santa Helenita Court Table */}
                  {(() => {
                    const santaHelenitaMatches = saturdayMatches.filter(match => {
                      const court = (courts || []).find(c => c.id === match.court_id);
                      return court && court.name.toLowerCase().includes('santa helenita');
                    });

                    return (
                      <div className="bg-gray-50 p-4 border">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cancha Santa Helenita</h3>
                        
            <div className="overflow-x-auto">
                          <table className="w-full border-collapse border border-gray-300">
                            <thead>
                              <tr className="bg-gray-200">
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Hora</th>
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Partido</th>
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Torneo</th>
                  </tr>
                </thead>
                            <tbody>
                              {santaHelenitaMatches
                                .sort((a, b) => {
                                  const timeSlotA = (timeSlots || []).find(ts => ts.id === a.time_slot_id);
                                  const timeSlotB = (timeSlots || []).find(ts => ts.id === b.time_slot_id);
                                  return timeSlotA && timeSlotB ? timeSlotA.start_time.localeCompare(timeSlotB.start_time) : 0;
                                })
                                .map((match) => {
                                  const team1 = (teams || []).find(t => t.id === match.team1_id);
                                  const team2 = (teams || []).find(t => t.id === match.team2_id);
                                  const tournament = (tournaments || []).find(t => t.id === team1?.tournament_id);
                                  const timeSlot = (timeSlots || []).find(ts => ts.id === match.time_slot_id);
                                  
                                  return (
                                    <tr key={match.id}>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {timeSlot ? formatTimeTo12Hour(timeSlot.start_time) : 'N/A'}
                                      </td>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {team1?.name || 'Unknown'} vs {team2?.name || 'Unknown'}
                        </td>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {tournament?.name || 'Unknown'}
                        </td>
                                    </tr>
                                  );
                                })}
                            </tbody>
                          </table>
                        </div>
                          </div>
                    );
                  })()}

                  {/* La Clarita Court Table */}
                  {(() => {
                    const laClaritaMatches = saturdayMatches.filter(match => {
                      const court = (courts || []).find(c => c.id === match.court_id);
                      return court && court.name.toLowerCase().includes('la clarita');
                    });

                    return (
                      <div className="bg-gray-50 p-4 border">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cancha La Clarita</h3>
                        
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse border border-gray-300">
                            <thead>
                              <tr className="bg-gray-200">
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Hora</th>
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Partido</th>
                                <th className="border border-gray-300 px-2 py-2 text-left text-xs font-semibold text-gray-900">Torneo</th>
                              </tr>
                            </thead>
                            <tbody>
                              {laClaritaMatches
                                .sort((a, b) => {
                                  const timeSlotA = (timeSlots || []).find(ts => ts.id === a.time_slot_id);
                                  const timeSlotB = (timeSlots || []).find(ts => ts.id === b.time_slot_id);
                                  return timeSlotA && timeSlotB ? timeSlotA.start_time.localeCompare(timeSlotB.start_time) : 0;
                                })
                                .map((match) => {
                                  const team1 = (teams || []).find(t => t.id === match.team1_id);
                                  const team2 = (teams || []).find(t => t.id === match.team2_id);
                                  const tournament = (tournaments || []).find(t => t.id === team1?.tournament_id);
                                  const timeSlot = (timeSlots || []).find(ts => ts.id === match.time_slot_id);
                                  
                                  return (
                                    <tr key={match.id}>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {timeSlot ? formatTimeTo12Hour(timeSlot.start_time) : 'N/A'}
                        </td>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {team1?.name || 'Unknown'} vs {team2?.name || 'Unknown'}
                        </td>
                                      <td className="border border-gray-300 px-2 py-2 text-xs text-gray-700">
                                        {tournament?.name || 'Unknown'}
                        </td>
                      </tr>
                                  );
                                })}
                </tbody>
              </table>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* Unscheduled Teams by Tournament */}
                {unscheduledTeams.length > 0 && (
                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                    <h3 className="text-lg font-medium text-yellow-800">Equipos No Programados</h3>
                    <p className="text-sm text-yellow-600 mt-1 mb-4">
                      {unscheduledTeams.length} equipos no tienen partidos programados para el sábado:
                    </p>
                    
                    {/* Group unscheduled teams by tournament */}
                    {(() => {
                      const teamsByTournament = unscheduledTeams.reduce((acc, team) => {
                        const tournament = tournaments.find(t => t.id === team.tournament_id)
                        const tournamentName = tournament?.name || 'Sin torneo'
                        if (!acc[tournamentName]) {
                          acc[tournamentName] = []
                        }
                        acc[tournamentName].push(team)
                        return acc
                      }, {} as Record<string, typeof unscheduledTeams>)
                      
                      return Object.entries(teamsByTournament).map(([tournamentName, teams]) => (
                        <div key={tournamentName} className="mb-4 last:mb-0">
                          <h4 className="text-sm font-semibold text-yellow-800 mb-2 flex items-center">
                            <span className="text-lg mr-2">🏆</span>
                            {tournamentName}
                            <span className="ml-2 text-xs bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full">
                              {teams.length} equipo{teams.length !== 1 ? 's' : ''}
                            </span>
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {teams.map(team => (
                              <span key={team.id} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                                {team.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))
                    })()}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No hay partidos programados para el sábado.</p>
                <button
                  onClick={createSaturdaySchedule}
                  disabled={isLoading}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {isLoading ? 'Creando...' : 'Crear Horario del Sábado'}
                </button>
            </div>
          )}
        </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Horario de Torneos del Sábado</h2>
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No hay horario generado para el sábado.</p>
              <button
                onClick={createSaturdaySchedule}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Creando...' : 'Crear Horario del Sábado'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}