'use client'

import React, { useState, useEffect } from 'react'

interface Team {
  id: string
  name: string
}

interface FixtureResult {
  team1_score: number
  team2_score: number
  status: 'pending' | 'scheduled' | 'completed'
  last_updated_by?: string
  last_updated_at?: string
}

interface TournamentFixtureTableProps {
  tournamentId: string
  teams: Team[]
  fixtures: any[]
  onResultUpdate: (fixtureId: string, team1Score: number, team2Score: number) => Promise<void>
}

export default function TournamentFixtureTable({
  tournamentId,
  teams,
  fixtures,
  onResultUpdate
}: TournamentFixtureTableProps) {
  const [editingCell, setEditingCell] = useState<{row: number, col: number} | null>(null)
  const [tempScores, setTempScores] = useState<{team1: string, team2: string}>({team1: '', team2: ''})
  const [fixtureResults, setFixtureResults] = useState<Map<string, FixtureResult>>(new Map())
  const [standings, setStandings] = useState<any[]>([])
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(Date.now())
  const [unsavedChanges, setUnsavedChanges] = useState<Map<string, {team1Score: number, team2Score: number}>>(new Map())
  const [isSaving, setIsSaving] = useState<boolean>(false)

  // Initialize fixture results from props
  useEffect(() => {
    console.log('TournamentFixtureTable: Fixtures prop changed, reinitializing fixtureResults')
    console.log('Fixtures data:', fixtures)
    
    // Clear unsaved changes when switching tournaments
    setUnsavedChanges(new Map())
    setEditingCell(null)
    setTempScores({team1: '', team2: ''})
    
    const resultsMap = new Map<string, FixtureResult>()
    fixtures.forEach(fixture => {
      // Handle both data structures: fixture.team1.id (old) and fixture.team1_id (new)
      const team1Id = fixture.team1?.id || fixture.team1_id
      const team2Id = fixture.team2?.id || fixture.team2_id
      
      if (!team1Id || !team2Id) {
        console.warn('Skipping fixture with missing team IDs:', fixture)
        return
      }
      
      const key1 = `${team1Id}-${team2Id}`
      const key2 = `${team2Id}-${team1Id}`
      const result = {
        team1_score: fixture.team1_score || 0,
        team2_score: fixture.team2_score || 0,
        status: fixture.status || 'pending',
        last_updated_by: fixture.last_updated_by,
        last_updated_at: fixture.last_updated_at
      }
      
      // Store in both directions for easy lookup
      resultsMap.set(key1, result)
      resultsMap.set(key2, {
        team1_score: fixture.team2_score || 0,
        team2_score: fixture.team1_score || 0,
        status: fixture.status || 'pending',
        last_updated_by: fixture.last_updated_by,
        last_updated_at: fixture.last_updated_at
      })
    })
    setFixtureResults(resultsMap)
  }, [fixtures, tournamentId]) // Remove lastUpdateTime dependency to avoid infinite loops

  // Calculate standings
  useEffect(() => {
    console.log('TournamentFixtureTable: Calculating standings')
    console.log('Current fixtureResults:', fixtureResults)
    
    const teamStats = teams.map(team => ({
      team,
      matchesPlayed: 0,
      wins: 0,
      losses: 0,
      pointsFor: 0,
      pointsAgainst: 0,
      pointsDifference: 0,
      points: 0  // Tournament points (2 for win, 1 for loss, 0 for forfeit)
    }))

    // Calculate stats for each team
    teams.forEach((team, teamIndex) => {
      teams.forEach((opponent, opponentIndex) => {
        if (teamIndex !== opponentIndex) {
          // Use getFixtureResult to get the result in the correct format
          // getFixtureResult returns: team1_score = row team score, team2_score = column team score
          const result = getFixtureResult(teamIndex, opponentIndex)
          
          if (result && result.status === 'completed') {
            teamStats[teamIndex].matchesPlayed++
            
            // team1_score is always the row team (current team) score
            // team2_score is always the column team (opponent) score
            teamStats[teamIndex].pointsFor += result.team1_score
            teamStats[teamIndex].pointsAgainst += result.team2_score
            
            if (result.team1_score > result.team2_score) {
              teamStats[teamIndex].wins++
              teamStats[teamIndex].points += 2  // 2 points for win
            } else if (result.team1_score < result.team2_score) {
              teamStats[teamIndex].losses++
              // Tournament points: 1 for regular loss, 0 for forfeit (0/20 score)
              if (result.team1_score === 0 && result.team2_score === 20) {
                teamStats[teamIndex].points += 0  // Forfeit (0/20)
              } else {
                teamStats[teamIndex].points += 1  // Regular loss
              }
            }
          }
        }
      })
      
      teamStats[teamIndex].pointsDifference = 
        teamStats[teamIndex].pointsFor - teamStats[teamIndex].pointsAgainst
    })

    // Sort by tournament points (desc), then points difference (desc)
    teamStats.sort((a, b) => {
      if (b.points !== a.points) return b.points - a.points
      return b.pointsDifference - a.pointsDifference
    })

    setStandings(teamStats)
  }, [teams, fixtureResults])

  const formatLastUpdate = (lastUpdatedAt: string | undefined, lastUpdatedBy: string | undefined): string => {
    if (!lastUpdatedAt || !lastUpdatedBy) return ''
    
    try {
      const date = new Date(lastUpdatedAt)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffHours / 24)
      
      if (diffDays > 0) {
        return `Actualizado hace ${diffDays} día${diffDays > 1 ? 's' : ''} por ${lastUpdatedBy}`
      } else if (diffHours > 0) {
        return `Actualizado hace ${diffHours} hora${diffHours > 1 ? 's' : ''} por ${lastUpdatedBy}`
      } else {
        const diffMinutes = Math.floor(diffMs / (1000 * 60))
        if (diffMinutes > 0) {
          return `Actualizado hace ${diffMinutes} minuto${diffMinutes > 1 ? 's' : ''} por ${lastUpdatedBy}`
        } else {
          return `Actualizado ahora por ${lastUpdatedBy}`
        }
      }
    } catch (error) {
      return `Actualizado por ${lastUpdatedBy}`
    }
  }

  const getFixtureResult = (team1Index: number, team2Index: number): FixtureResult | null => {
    if (team1Index === team2Index) return null // Same team
    
    const team1 = teams[team1Index]
    const team2 = teams[team2Index]
    
    if (!team1 || !team2) return null
    
    // Try both possible key combinations since fixtures can be stored either way
    const key1 = `${team1.id}-${team2.id}`
    const key2 = `${team2.id}-${team1.id}`
    
    let result = fixtureResults.get(key1)
    if (!result) {
      result = fixtureResults.get(key2)
      // If we found the result with reversed key, we need to swap the scores
      // so that team1_score always refers to the row team (team1Index) and team2_score to the column team (team2Index)
      if (result) {
        result = {
          team1_score: result.team2_score, // row team gets the score that was stored as team2_score
          team2_score: result.team1_score, // column team gets the score that was stored as team1_score
          status: result.status,
          last_updated_by: result.last_updated_by,
          last_updated_at: result.last_updated_at
        }
      }
    }
    return result || { team1_score: 0, team2_score: 0, status: 'pending' }
  }

  const handleCellClick = (row: number, col: number) => {
    if (row === col) return // Can't edit diagonal cells
    
    const result = getFixtureResult(row, col)
    if (result) {
      setEditingCell({row, col})
      
      // Determine which score belongs to the row team vs column team
      const rowTeam = teams[row]
      const colTeam = teams[col]
      
      // Find the original fixture to determine the correct score mapping
      const originalFixture = fixtures.find(f => {
        const fTeam1Id = f.team1?.id || f.team1_id
        const fTeam2Id = f.team2?.id || f.team2_id
        return (fTeam1Id === rowTeam.id && fTeam2Id === colTeam.id) ||
               (fTeam1Id === colTeam.id && fTeam2Id === rowTeam.id)
      })
      
      let rowTeamScore, colTeamScore
      if (originalFixture) {
        const originalTeam1Id = originalFixture.team1?.id || originalFixture.team1_id
        if (originalTeam1Id === rowTeam.id) {
          rowTeamScore = result.team1_score
          colTeamScore = result.team2_score
        } else {
          rowTeamScore = result.team2_score
          colTeamScore = result.team1_score
        }
      } else {
        // Fallback if fixture not found
        rowTeamScore = result.team1_score
        colTeamScore = result.team2_score
      }
      
      setTempScores({
        team1: rowTeamScore.toString(),
        team2: colTeamScore.toString()
      })
    }
  }

  const handleSaveResult = () => {
    if (!editingCell) return
    
    const team1Index = editingCell.row
    const team2Index = editingCell.col
    const team1 = teams[team1Index]
    const team2 = teams[team2Index]
    
    const team1Score = parseInt(tempScores.team1) || 0
    const team2Score = parseInt(tempScores.team2) || 0
    
    // Find the fixture using team IDs (handle both data structures)
    let fixture = fixtures.find(f => {
      const fTeam1Id = f.team1?.id || f.team1_id
      const fTeam2Id = f.team2?.id || f.team2_id
      return (fTeam1Id === team1.id && fTeam2Id === team2.id) ||
             (fTeam1Id === team2.id && fTeam2Id === team1.id)
    })
    
    // If not found by ID, try by team names
    if (!fixture) {
      fixture = fixtures.find(f => {
        const fTeam1Name = f.team1?.name || f.team1_name
        const fTeam2Name = f.team2?.name || f.team2_name
        return (fTeam1Name === team1.name && fTeam2Name === team2.name) ||
               (fTeam1Name === team2.name && fTeam2Name === team1.name)
      })
    }
    
    if (!fixture) {
      alert('Error: No se encontró el fixture para estos equipos')
      return
    }
    
    // Check if we're overwriting existing scores
    const hasExistingScores = (fixture.team1_score > 0 || fixture.team2_score > 0)
    const isChangingScores = (fixture.team1_score !== team1Score || fixture.team2_score !== team2Score)
    
    if (hasExistingScores && isChangingScores) {
      const lastUpdateInfo = formatLastUpdate(fixture.last_updated_at, fixture.last_updated_by)
      const confirmMessage = `⚠️ ADVERTENCIA: Estás a punto de sobrescribir puntuaciones existentes.\n\n` +
        `Puntuación actual: ${fixture.team1_score}-${fixture.team2_score}\n` +
        `Nueva puntuación: ${team1Score}-${team2Score}\n\n` +
        `${lastUpdateInfo}\n\n` +
        `¿Estás seguro de que quieres continuar?`
      
      if (!confirm(confirmMessage)) {
        return // User cancelled
      }
    }
    
    // Always use the row/column perspective for consistency
    // team1Score = row team score, team2Score = column team score
    // We need to map this to the fixture's team1/team2 format for the API
    let finalTeam1Score, finalTeam2Score
    
    // Handle both data structures: fixture.team1.id (old) and fixture.team1_id (new)
    const fixtureTeam1Id = fixture.team1?.id || fixture.team1_id
    const fixtureTeam2Id = fixture.team2?.id || fixture.team2_id
    
    if (fixtureTeam1Id === team1.id || fixture.team1?.name === team1.name) {
      // Row team is team1 in fixture
      finalTeam1Score = team1Score  // row team score
      finalTeam2Score = team2Score  // column team score
    } else {
      // Row team is team2 in fixture, so we need to swap
      finalTeam1Score = team2Score  // column team score becomes team1
      finalTeam2Score = team1Score  // row team score becomes team2
    }
    
    // Store the change locally instead of saving immediately
    const newUnsavedChanges = new Map(unsavedChanges)
    newUnsavedChanges.set(fixture.id, {
      team1Score: finalTeam1Score,
      team2Score: finalTeam2Score
    })
    setUnsavedChanges(newUnsavedChanges)
    
    // Update local display immediately using row/column perspective
    const key1 = `${team1.id}-${team2.id}`
    const key2 = `${team2.id}-${team1.id}`
    const newResults = new Map(fixtureResults)
    
    // Always store in row/column format for consistency
    // key1: row team vs column team
    newResults.set(key1, {
      team1_score: team1Score,  // row team score
      team2_score: team2Score,  // column team score
      status: 'completed'
    })
    // key2: column team vs row team (swapped)
    newResults.set(key2, {
      team1_score: team2Score,  // column team score
      team2_score: team1Score,  // row team score
      status: 'completed'
    })
    
    setFixtureResults(newResults)
    
    setEditingCell(null)
    setTempScores({team1: '', team2: ''})
  }

  const handleCancelEdit = () => {
    setEditingCell(null)
    setTempScores({team1: '', team2: ''})
  }

  const handleSaveAllChanges = async () => {
    if (unsavedChanges.size === 0) {
      alert('No hay cambios para guardar')
      return
    }

    setIsSaving(true)
    
    try {
      // Save all unsaved changes to the database
      const savePromises = Array.from(unsavedChanges.entries()).map(async ([fixtureId, scores]) => {
        console.log(`Saving fixture ${fixtureId} with scores:`, scores)
        await onResultUpdate(fixtureId, scores.team1Score, scores.team2Score)
      })

      await Promise.all(savePromises)
      
      // Clear unsaved changes after successful save
      setUnsavedChanges(new Map())
      
      alert(`Se guardaron ${unsavedChanges.size} cambios exitosamente`)
      
    } catch (error) {
      console.error('Error saving changes:', error)
      alert('Error al guardar los cambios: ' + (error instanceof Error ? error.message : 'Error desconocido'))
    } finally {
      setIsSaving(false)
    }
  }

  const renderCell = (row: number, col: number) => {
    if (row === col) {
      // Diagonal cell - show team name
      return (
        <td className="w-24 h-12 bg-gray-100 border border-gray-300 text-center text-xs font-medium text-gray-600">
          {teams[row]?.name || ''}
        </td>
      )
    }

    const result = getFixtureResult(row, col)
    const isEditing = editingCell?.row === row && editingCell?.col === col
    
    if (isEditing) {
      return (
        <td className="w-24 h-12 border border-gray-300 bg-yellow-50">
          <div className="flex flex-col h-full">
            <div className="flex h-1/2">
              <input
                type="number"
                value={tempScores.team1}
                onChange={(e) => setTempScores({...tempScores, team1: e.target.value})}
                className="w-1/2 h-full text-center text-xs border-0 bg-transparent focus:outline-none"
                placeholder="0"
                autoFocus
              />
              <input
                type="number"
                value={tempScores.team2}
                onChange={(e) => setTempScores({...tempScores, team2: e.target.value})}
                className="w-1/2 h-full text-center text-xs border-0 bg-transparent focus:outline-none"
                placeholder="0"
              />
            </div>
            <div className="flex h-1/2">
              <button
                onClick={handleSaveResult}
                className="w-1/2 h-full bg-green-500 text-white text-xs hover:bg-green-600"
              >
                ✓
              </button>
              <button
                onClick={handleCancelEdit}
                className="w-1/2 h-full bg-red-500 text-white text-xs hover:bg-red-600"
              >
                ✗
              </button>
            </div>
          </div>
        </td>
      )
    }

    if (result && result.status === 'completed') {
      // getFixtureResult now returns scores in the correct format:
      // team1_score = row team score, team2_score = column team score
      const lastUpdateInfo = formatLastUpdate(result.last_updated_at, result.last_updated_by)
      
      // Check if this was updated recently (within last hour)
      const isRecentlyUpdated = result.last_updated_at && 
        (new Date().getTime() - new Date(result.last_updated_at).getTime()) < (60 * 60 * 1000)
      
      
      return (
        <td 
          className={`w-24 h-12 border border-gray-300 cursor-pointer hover:bg-green-100 text-center text-xs relative group ${
            isRecentlyUpdated ? 'bg-green-100 ring-2 ring-green-300' : 'bg-green-50'
          }`}
          onClick={() => handleCellClick(row, col)}
          title={lastUpdateInfo}
        >
          <div className="flex h-full items-center justify-center">
            <span className="font-medium">
              {Number(result.team1_score)}/{Number(result.team2_score)}
            </span>
            {/* Recent update indicator */}
            {isRecentlyUpdated && (
              <div className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            )}
          </div>
          {/* Tooltip - Temporarily disabled to test */}
          {/* {lastUpdateInfo && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10">
              {lastUpdateInfo}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
            </div>
          )} */}
        </td>
      )
    }

    // Pending game
    return (
      <td 
        className="w-24 h-12 border border-gray-300 bg-yellow-100 cursor-pointer hover:bg-yellow-200 text-center text-xs"
        onClick={() => handleCellClick(row, col)}
      >
        <div className="flex h-full items-center justify-center">
          <span className="text-gray-500">-</span>
        </div>
      </td>
    )
  }

  return (
    <div className="bg-white p-4 border rounded-lg">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Fixture del Torneo</h3>
      
      <div className="overflow-x-auto">
        <table className="border-collapse border border-gray-300 text-xs">
          <thead>
            <tr>
              <th className="w-8 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                #
              </th>
              <th className="w-32 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                Equipos
              </th>
              {teams.map((team, index) => (
                <th key={team.id} className="w-24 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                  {index + 1}
                </th>
              ))}
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                P.G.
              </th>
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                P.P.
              </th>
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                P.F.
              </th>
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                P.C.
              </th>
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                Dif.
              </th>
              <th className="w-16 h-12 bg-gray-100 border border-gray-300 text-center font-medium text-gray-700">
                Pos.
              </th>
            </tr>
          </thead>
          <tbody>
            {teams.map((team, rowIndex) => {
              const teamStanding = standings.find(s => s.team.id === team.id)
              return (
                <tr key={team.id}>
                  <td className="w-8 h-12 bg-gray-50 border border-gray-300 text-center font-bold text-gray-700">
                    {rowIndex + 1}
                  </td>
                  <td className="w-32 h-12 bg-gray-50 border border-gray-300 text-center font-medium text-gray-700">
                    {team.name}
                  </td>
                  {teams.map((_, colIndex) => renderCell(rowIndex, colIndex))}
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {teamStanding?.wins || 0}
                  </td>
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {teamStanding?.losses || 0}
                  </td>
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {teamStanding?.pointsFor || 0}
                  </td>
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {teamStanding?.pointsAgainst || 0}
                  </td>
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {teamStanding?.pointsDifference || 0}
                  </td>
                  <td className="w-16 h-12 bg-gray-50 border border-gray-300 text-center font-medium">
                    {standings.findIndex(s => s.team.id === team.id) + 1}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 text-xs text-gray-600">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-50 border border-green-300"></div>
            <span>Partido jugado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300"></div>
            <span>Partido pendiente</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-50 border border-yellow-300"></div>
            <span>Editando resultado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-100 border-2 border-green-300"></div>
            <span>Actualizado recientemente</span>
          </div>
        </div>
        <p className="mt-2">Haz clic en una celda para editar el resultado del partido.</p>
        
        {/* Last update summary */}
        {(() => {
          const completedFixtures = fixtures.filter(f => f.status === 'completed' && f.last_updated_at)
          if (completedFixtures.length > 0) {
            const mostRecent = completedFixtures.reduce((latest, current) => 
              new Date(current.last_updated_at) > new Date(latest.last_updated_at) ? current : latest
            )
            const lastUpdateInfo = formatLastUpdate(mostRecent.last_updated_at, mostRecent.last_updated_by)
            return (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                <span className="text-blue-800 font-medium">Última actualización:</span> {lastUpdateInfo}
              </div>
            )
          }
          return null
        })()}
        
        {/* Save Button */}
        {unsavedChanges.size > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                <span className="text-sm text-yellow-800">
                  Tienes {unsavedChanges.size} cambio{unsavedChanges.size > 1 ? 's' : ''} sin guardar
                </span>
              </div>
              <button
                onClick={handleSaveAllChanges}
                disabled={isSaving}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  isSaving
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500'
                }`}
              >
                {isSaving ? 'Guardando...' : 'Guardar Cambios'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
