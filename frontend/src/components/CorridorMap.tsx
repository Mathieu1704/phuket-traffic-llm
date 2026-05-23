'use client';

import { useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, Tooltip, Marker } from 'react-leaflet';
import L from 'leaflet';
import type { Corridor } from '@/lib/types';

const OWM_KEY = process.env.NEXT_PUBLIC_OWM_API_KEY ?? '';

const OWM_LAYERS = [
  { id: 'temp_new',          label: 'Temperature', icon: '🌡️', color: 'rgba(239,68,68,0.7)'   },
  { id: 'precipitation_new', label: 'Rain',         icon: '🌧',  color: 'rgba(59,130,246,0.7)'  },
  { id: 'wind_new',          label: 'Wind',         icon: '💨',  color: 'rgba(34,197,94,0.7)'   },
  { id: 'clouds_new',        label: 'Clouds',       icon: '☁️',  color: 'rgba(148,163,184,0.7)' },
] as const;

type LayerId = typeof OWM_LAYERS[number]['id'] | null;

// Weather station markers (5 Phuket locations)
const WEATHER_STATIONS = [
  { id: 'airport',     name: 'HKT Airport',  lat: 8.113,  lon: 98.302, temp: 31, icon: '⛅', condition: 'Partly cloudy', rain_mm: 8,  wind_kmh: 16, humidity: 74 },
  { id: 'patong',      name: 'Patong Beach',  lat: 7.900,  lon: 98.298, temp: 30, icon: '🌧', condition: 'Light rain',    rain_mm: 28, wind_kmh: 22, humidity: 85 },
  { id: 'phuket_town', name: 'Phuket Town',   lat: 7.885,  lon: 98.400, temp: 32, icon: '🌤', condition: 'Mostly sunny',  rain_mm: 4,  wind_kmh: 12, humidity: 68 },
  { id: 'rawai',       name: 'Rawai',          lat: 7.781,  lon: 98.332, temp: 29, icon: '🌦', condition: 'Showers',       rain_mm: 18, wind_kmh: 19, humidity: 82 },
  { id: 'chalong',     name: 'Chalong',        lat: 7.843,  lon: 98.349, temp: 31, icon: '⛅', condition: 'Partly cloudy', rain_mm: 6,  wind_kmh: 14, humidity: 76 },
];

type Station = typeof WEATHER_STATIONS[0];

function makeWeatherIcon(s: Station) {
  const html = `
    <div style="
      background: rgba(15,20,35,0.88);
      border: 1px solid rgba(255,255,255,0.14);
      border-radius: 16px;
      padding: 9px 12px 8px;
      box-shadow: 0 6px 24px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.07);
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      white-space: nowrap;
    ">
      <div style="display:flex; align-items:center; gap:5px; margin-bottom:3px">
        <span style="font-size:21px; line-height:1">${s.icon}</span>
        <span style="font-size:26px; font-weight:700; color:#fff; letter-spacing:-1.5px; line-height:1">${s.temp}°</span>
      </div>
      <div style="font-size:10px; color:rgba(255,255,255,0.5); font-weight:500; margin-bottom:5px">${s.name}</div>
      <div style="display:flex; gap:8px; font-size:9px; color:rgba(255,255,255,0.35)">
        <span>💧${s.rain_mm}mm</span>
        <span>💨${s.wind_kmh}km/h</span>
        <span>💦${s.humidity}%</span>
      </div>
    </div>
  `;
  return L.divIcon({ html, className: '', iconSize: [116, 72], iconAnchor: [58, 36] });
}

interface MapProps {
  corridors: Corridor[];
  selectedId?: number | null;
  onSelect?: (id: number) => void;
}

export default function CorridorMap({ corridors, selectedId, onSelect }: MapProps) {
  const [activeLayer, setActiveLayer] = useState<LayerId>(null);
  const [showStations, setShowStations] = useState(true);

  const toggleLayer = (id: typeof OWM_LAYERS[number]['id']) =>
    setActiveLayer((prev) => (prev === id ? null : id));

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer center={[7.96, 98.345]} zoom={11} style={{ width: '100%', height: '100%' }}>
        {/* Base dark tiles */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
        />

        {/* OWM weather overlay */}
        {activeLayer && OWM_KEY && (
          <TileLayer
            key={activeLayer}
            url={`https://tile.openweathermap.org/map/${activeLayer}/{z}/{x}/{y}.png?appid=${OWM_KEY}`}
            opacity={1}
            className="owm-overlay"
            attribution='<a href="https://openweathermap.org">OpenWeatherMap</a>'
          />
        )}

        {/* Traffic corridors */}
        {corridors.map((c) => {
          const isSelected = selectedId === c.id;
          return (
            <Polyline
              key={c.id}
              positions={c.polyline}
              pathOptions={{
                color: c.color,
                weight: isSelected ? 6 : 4,
                opacity: isSelected ? 1 : selectedId != null ? 0.4 : 0.85,
              }}
              eventHandlers={{ click: () => onSelect?.(c.id) }}
            />
          );
        })}

        {/* Corridor endpoint markers */}
        {corridors.map((c) => {
          const isSelected = selectedId === c.id;
          const alpha = isSelected || selectedId == null ? 1 : 0.35;
          return c.polyline
            .filter((_, i) => i === 0 || i === c.polyline.length - 1)
            .map((pos, i) => (
              <CircleMarker
                key={`${c.id}-${i}`}
                center={pos}
                radius={isSelected ? 7 : 5}
                pathOptions={{ color: c.color, fillColor: c.color, fillOpacity: alpha, weight: 2 }}
                eventHandlers={{ click: () => onSelect?.(c.id) }}
              >
                {i === 0 && (
                  <Tooltip permanent={isSelected} direction="top">
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{c.name}</span>
                  </Tooltip>
                )}
                <Popup>
                  <div style={{ minWidth: 180 }}>
                    <p style={{ fontWeight: 700, marginBottom: 4 }}>{c.name}</p>
                    <p style={{ color: '#888', fontSize: 12, marginBottom: 8 }}>{c.description}</p>
                    <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
                      <tbody>
                        {[
                          ['Avg PTI',      c.pti_mean.toFixed(2)],
                          ['TTR AM peak',  c.tt_ratio_am.toFixed(2)],
                          ['Median speed', `${c.spd_median_kmh} km/h`],
                          ['Length',       `${c.length_km} km`],
                        ].map(([k, v]) => (
                          <tr key={k}>
                            <td style={{ color: '#888', paddingRight: 8, paddingBottom: 2 }}>{k}</td>
                            <td style={{ fontWeight: 600 }}>{v}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Popup>
              </CircleMarker>
            ));
        })}

        {/* Weather station markers */}
        {showStations && WEATHER_STATIONS.map((s) => (
          <Marker key={s.id} position={[s.lat, s.lon]} icon={makeWeatherIcon(s)}>
            <Popup>
              <div style={{ minWidth: 160, fontFamily: '-apple-system, sans-serif' }}>
                <p style={{ fontWeight: 700, fontSize: 14, marginBottom: 2 }}>{s.name}</p>
                <p style={{ color: '#888', fontSize: 11, marginBottom: 8 }}>{s.condition}</p>
                <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
                  <tbody>
                    {[
                      ['Temperature', `${s.temp}°C`],
                      ['Rainfall',    `${s.rain_mm} mm`],
                      ['Wind',        `${s.wind_kmh} km/h`],
                      ['Humidity',    `${s.humidity}%`],
                    ].map(([k, v]) => (
                      <tr key={k}>
                        <td style={{ color: '#888', paddingRight: 10, paddingBottom: 3 }}>{k}</td>
                        <td style={{ fontWeight: 600 }}>{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Floating controls — top right */}
      <div style={{
        position: 'absolute', top: 12, right: 12, zIndex: 1000,
        display: 'flex', flexDirection: 'column', gap: 6,
        fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
      }}>
        {/* OWM layer buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {OWM_LAYERS.map((layer) => {
            const active = activeLayer === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => toggleLayer(layer.id)}
                style={{
                  background: active ? layer.color : 'rgba(15,20,35,0.82)',
                  border: `1px solid ${active ? 'rgba(255,255,255,0.25)' : 'rgba(255,255,255,0.11)'}`,
                  borderRadius: 9,
                  padding: '5px 11px',
                  color: '#fff',
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  backdropFilter: 'blur(10px)',
                  boxShadow: active ? '0 2px 12px rgba(0,0,0,0.5)' : '0 1px 6px rgba(0,0,0,0.3)',
                  transition: 'all 0.15s ease',
                  minWidth: 110,
                }}
              >
                <span style={{ fontSize: 13 }}>{layer.icon}</span>
                {layer.label}
                {active && <span style={{ marginLeft: 'auto', fontSize: 9, opacity: 0.7 }}>ON</span>}
              </button>
            );
          })}
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: 'rgba(255,255,255,0.08)', margin: '2px 0' }} />

        {/* Station markers toggle */}
        <button
          onClick={() => setShowStations((v) => !v)}
          style={{
            background: showStations ? 'rgba(15,20,35,0.88)' : 'rgba(15,20,35,0.55)',
            border: `1px solid ${showStations ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.07)'}`,
            borderRadius: 9,
            padding: '5px 11px',
            color: showStations ? '#fff' : 'rgba(255,255,255,0.35)',
            fontSize: 11,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            backdropFilter: 'blur(10px)',
            boxShadow: '0 1px 6px rgba(0,0,0,0.3)',
            transition: 'all 0.15s ease',
            minWidth: 110,
          }}
        >
          <span style={{ fontSize: 13 }}>📍</span>
          Stations
        </button>
      </div>

      {/* Legend — bottom left, visible when a layer is active */}
      {activeLayer && (
        <div style={{
          position: 'absolute', bottom: 24, left: 12, zIndex: 1000,
          background: 'rgba(15,20,35,0.88)',
          border: '1px solid rgba(255,255,255,0.11)',
          borderRadius: 10,
          padding: '8px 12px',
          backdropFilter: 'blur(10px)',
          fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
        }}>
          <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 9, fontWeight: 600, marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {OWM_LAYERS.find(l => l.id === activeLayer)?.label} layer
          </p>
          {activeLayer === 'temp_new' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>−40°</span>
              <div style={{ width: 80, height: 8, borderRadius: 4, background: 'linear-gradient(to right, #4575b4, #91bfdb, #e0f3f8, #fee090, #fc8d59, #d73027)' }} />
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>+40°</span>
            </div>
          )}
          {activeLayer === 'precipitation_new' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>0</span>
              <div style={{ width: 80, height: 8, borderRadius: 4, background: 'linear-gradient(to right, transparent, #a8edea, #3b82f6, #7c3aed)' }} />
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>heavy</span>
            </div>
          )}
          {activeLayer === 'wind_new' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>calm</span>
              <div style={{ width: 80, height: 8, borderRadius: 4, background: 'linear-gradient(to right, #22c55e, #eab308, #ef4444)' }} />
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>strong</span>
            </div>
          )}
          {activeLayer === 'clouds_new' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>clear</span>
              <div style={{ width: 80, height: 8, borderRadius: 4, background: 'linear-gradient(to right, transparent, rgba(148,163,184,0.5), rgba(148,163,184,1))' }} />
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.4)' }}>overcast</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
