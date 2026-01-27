<script lang="ts" setup>
import {formatDate, getReplayUrl} from '@/utils/utils.ts'
import type {Match, Player, ReplayMeta} from '@/types/db-json'

defineProps<{
  match: Match & { metadata: ReplayMeta }
  filename: string
}>()

function getPlayerSteamProfileLink(player: Player): string {
  return `https://steamcommunity.com/profiles/${player.steam_id}`
}

function getMapWorkshopLink(replayMeta: ReplayMeta): string {
  return `https://steamcommunity.com/sharedfiles/filedetails/?id=${replayMeta.map_steam_id}`
}
</script>

<template>
  <div class="match-row">
    <div class="cell date">
      {{ formatDate(match.finished_at) }}
    </div>

    <div class="cell mode">
      {{ match.metadata.game_mode }}
    </div>

    <div class="cell download">
      <a v-if="match.downloadable" :href="getReplayUrl(filename)">Download</a>
      <span v-else class="disabled">—</span>
    </div>

    <div :class="{ highlighted: match.metadata.marker_count > 0 }" class="cell marker-count">
      {{ match.metadata.marker_count }}
    </div>

    <div :title="match.metadata.map_title" class="cell map">
      <a :href="getMapWorkshopLink(match.metadata)" target="_blank">
        {{ match.metadata.map_title }}
      </a>
    </div>

    <div class="cell players">
      <div class="players-scroll">
        <div v-for="player in match.metadata.players" :key="player.steam_id" class="player">
          <a :href="getPlayerSteamProfileLink(player)" class="player-name" target="_blank">
            {{ player.name }}
          </a>
          <span class="score">{{ player.score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.players {
  overflow: hidden;
}

.players-scroll {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
}

.player {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;

  padding: 0.1rem 0.4rem;
  border: 1px solid #ddd;
  border-radius: 4px;

  font-size: 0.85em;
  background: #fafafa;
}

.player-name {
  max-width: 16ch;
  overflow: hidden;
  text-overflow: ellipsis;
}

.disabled {
  color: #aaa;
}

.marker-count.highlighted {
  font-weight: 600;
  color: #333;
}
</style>
