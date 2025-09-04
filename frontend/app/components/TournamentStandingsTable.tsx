'use client'

import { useState, useEffect } from 'react'

interface Team {
  id: string
  name: string
}

interface Fixture {
  fixture_id: string
  team1: Team
  team2: Team
  team1_score: number
  team2_score: number
  status: string
}

interface TeamStats {
  team: Team
  matchesPlayed: number
  wins: number
  losses: number
  forfeits: number  // Games lost with 0/20 score
  pointsFor: number
  pointsAgainst: number
  pointsDifference: number
  points: number  // Tournament points (2 for win, 1 for loss, 0 for forfeit)
  position: number
}

interface TournamentStandingsTableProps {
  tournamentId: string
  teams: Team[]
  fixtures: Fixture[]
}

export default function TournamentStandingsTable({ 
  tournamentId, 
  teams, 
  fixtures 
}: TournamentStandingsTableProps) {
  const [standings, setStandings] = useState<TeamStats[]>([])

  // Calculate standings from fixtures
  useEffect(() => {
    console.log('TournamentStandingsTable: Calculating standings')
    console.log('Teams:', teams)
    console.log('Fixtures:', fixtures)
    
    const teamStats: TeamStats[] = teams.map(team => ({
      team,
      matchesPlayed: 0,
      wins: 0,
      losses: 0,
      forfeits: 0,  // Games lost with 0/20 score
      pointsFor: 0,
      pointsAgainst: 0,
      pointsDifference: 0,
      points: 0,  // Tournament points (2 for win, 1 for loss, 0 for forfeit)
      position: 0
    }))

    // Calculate stats for each team
    teams.forEach((team, teamIndex) => {
      teams.forEach((opponent, opponentIndex) => {
        if (teamIndex !== opponentIndex) {
          // Find the fixture between these teams
          const fixture = fixtures.find(f => {
            const fTeam1Id = f.team1?.id || f.team1_id
            const fTeam2Id = f.team2?.id || f.team2_id
            return (fTeam1Id === team.id && fTeam2Id === opponent.id) ||
                   (fTeam1Id === opponent.id && fTeam2Id === team.id)
          })
          
          if (fixture && fixture.status === 'completed') {
            teamStats[teamIndex].matchesPlayed++
            
            // Determine which team is team1 and which is team2 in the fixture
            let teamScore: number, opponentScore: number
            const fixtureTeam1Id = fixture.team1?.id || fixture.team1_id
            if (fixtureTeam1Id === team.id) {
              teamScore = fixture.team1_score
              opponentScore = fixture.team2_score
            } else {
              teamScore = fixture.team2_score
              opponentScore = fixture.team1_score
            }
            
            // Handle forfeits (0/20) differently
            if (teamScore === 0 && opponentScore === 20) {
              // Team lost by forfeit - don't add points to P.C. (Points Against)
              teamStats[teamIndex].forfeits++
              teamStats[teamIndex].points += 0  // 0 points for forfeit
              // Don't add opponentScore to pointsAgainst for forfeit losses
            } else if (teamScore === 20 && opponentScore === 0) {
              // Team won by forfeit - add points to P.F. (Points For)
              teamStats[teamIndex].pointsFor += teamScore
              teamStats[teamIndex].wins++
              teamStats[teamIndex].points += 2  // 2 points for win
              // Don't add opponentScore to pointsAgainst for forfeit wins
            } else {
              // Regular game - add points normally
              teamStats[teamIndex].pointsFor += teamScore
              teamStats[teamIndex].pointsAgainst += opponentScore
              
              if (teamScore > opponentScore) {
                teamStats[teamIndex].wins++
                teamStats[teamIndex].points += 2  // 2 points for win
              } else if (teamScore < opponentScore) {
                teamStats[teamIndex].losses++  // Regular loss
                teamStats[teamIndex].points += 1  // 1 point for regular loss
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

    // Assign positions
    teamStats.forEach((team, index) => {
      team.position = index + 1
    })

    console.log('Calculated standings:', teamStats)
    setStandings(teamStats)
  }, [teams, fixtures, tournamentId])

  if (standings.length === 0) {
    return (
      <div className="bg-white p-6 border rounded-lg">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Tabla de Posiciones</h4>
        <p className="text-gray-500">No hay datos suficientes para mostrar la tabla de posiciones.</p>
      </div>
    )
  }

  return (
    <div className="bg-white p-6 border rounded-lg">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">Tabla de Posiciones</h4>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pos.
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Equipo
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                P.J.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                P.G.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                P.P.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                W.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                P.F.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                P.C.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Dif.
              </th>
              <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pts.
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {standings.map((teamStats, index) => (
              <tr 
                key={teamStats.team.id}
                className={`${
                  index < 3 ? 'bg-yellow-50' : 
                  index >= standings.length - 2 ? 'bg-red-50' : 
                  'hover:bg-gray-50'
                }`}
              >
                <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    teamStats.position === 1 ? 'bg-yellow-100 text-yellow-800' :
                    teamStats.position === 2 ? 'bg-gray-100 text-gray-800' :
                    teamStats.position === 3 ? 'bg-orange-100 text-orange-800' :
                    teamStats.position >= standings.length - 1 ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {teamStats.position}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                  {teamStats.team.name}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  {teamStats.matchesPlayed}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  <span className="text-green-600 font-medium">{teamStats.wins}</span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  <span className="text-red-600 font-medium">{teamStats.losses}</span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  <span className="text-orange-600 font-medium">{teamStats.forfeits}</span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  {teamStats.pointsFor}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  {teamStats.pointsAgainst}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  <span className={`font-medium ${
                    teamStats.pointsDifference > 0 ? 'text-green-600' :
                    teamStats.pointsDifference < 0 ? 'text-red-600' :
                    'text-gray-500'
                  }`}>
                    {teamStats.pointsDifference > 0 ? '+' : ''}{teamStats.pointsDifference}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 text-center">
                  <span className="text-blue-600 font-bold text-lg">{teamStats.points}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      

      {/* Column explanations */}
      <div className="mt-3 text-xs text-gray-500">
        <p><strong>P.J.</strong> = Partidos Jugados | <strong>P.G.</strong> = Partidos Ganados | <strong>P.P.</strong> = Partidos Perdidos | <strong>W.</strong> = Walkover (0/20)</p>
        <p><strong>P.F.</strong> = Puntos a Favor | <strong>P.C.</strong> = Puntos en Contra | <strong>Dif.</strong> = Diferencia de Puntos</p>
        <p><strong>Pts.</strong> = Puntos del Torneo (2 por victoria, 1 por derrota, 0 por forfeit 0/20)</p>
      </div>
    </div>
  )
}
