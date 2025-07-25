import axios from "axios";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import React, { useEffect, useRef } from "react";

const ORS_API_KEY = "5b3ce3597851110001cf6248394a589885fe4531a3974bc055973b99";

const MapComponent = ({ latitude, longitude, places, selectedPlace }) => {
    const mapRef = useRef(null);
    const userMarkerRef = useRef(null);
    const routeLayerRef = useRef(null);
    const placeMarkersRef = useRef([]);

    // Initialize map and user marker
    useEffect(() => {
        if (!mapRef.current) {
            mapRef.current = L.map("map").setView([latitude, longitude], 14);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: "© OpenStreetMap contributors",
            }).addTo(mapRef.current);
        }

        if (userMarkerRef.current) mapRef.current.removeLayer(userMarkerRef.current);
        const userIcon = L.icon({ iconUrl: "/icons/minecraft.png", iconSize: [38, 38] });
        userMarkerRef.current = L.marker([latitude, longitude], { icon: userIcon })
            .addTo(mapRef.current)
            .bindPopup("You are here");
    }, [latitude, longitude]);

    // Update markers for suggested places
    useEffect(() => {
        placeMarkersRef.current.forEach((marker) => mapRef.current.removeLayer(marker));
        placeMarkersRef.current = [];

        if (!places || places.length === 0) return;

        places.forEach((place) => {
            const { geocodes, name, location } = place;
            if (geocodes?.main) {
                const placeIcon = L.icon({
                    iconUrl: "/icons/heart.png",
                    iconSize: [30, 30],
                });
                const marker = L.marker([geocodes.main.latitude, geocodes.main.longitude], {
                    icon: placeIcon,
                })
                    .addTo(mapRef.current)
                    .bindPopup(`<b>${name}</b><br>${location?.formatted_address || "No address"}`);
                placeMarkersRef.current.push(marker);
            }
        });

        const allLatLngs = [
            [latitude, longitude],
            ...places.map((p) => [p.geocodes.main.latitude, p.geocodes.main.longitude]),
        ];
        mapRef.current.fitBounds(allLatLngs);
    }, [places, latitude, longitude]);

    // Draw route to selected place
    useEffect(() => {
        const drawRoute = async () => {
            if (!selectedPlace || !selectedPlace.geocodes?.main) return;

            const start = [longitude, latitude];
            const end = [
                selectedPlace.geocodes.main.longitude,
                selectedPlace.geocodes.main.latitude,
            ];

            try {
                const res = await axios.post(
                    "https://api.openrouteservice.org/v2/directions/driving-car",
                    { coordinates: [start, end] },
                    { headers: { Authorization: ORS_API_KEY, "Content-Type": "application/json" } }
                );

                const coords = res.data.features[0].geometry.coordinates;
                const latlngs = coords.map(([lng, lat]) => [lat, lng]);

                if (routeLayerRef.current) mapRef.current.removeLayer(routeLayerRef.current);
                routeLayerRef.current = L.polyline(latlngs, { color: "blue", weight: 4 }).addTo(mapRef.current);
                mapRef.current.fitBounds(routeLayerRef.current.getBounds());
            } catch (error) {
                console.error("Error fetching route:", error);
            }
        };
        drawRoute();
    }, [selectedPlace, latitude, longitude]);

    // Reset map to current location
    const resetMap = () => {
        if (routeLayerRef.current) mapRef.current.removeLayer(routeLayerRef.current);
        placeMarkersRef.current.forEach((marker) => mapRef.current.removeLayer(marker));
        placeMarkersRef.current = [];

        mapRef.current.setView([latitude, longitude], 14);
    };

    return (
        <div style={{ position: "relative" }}>
            <div id="map" style={{ height: "500px", width: "100%" }} />
            <button
                onClick={resetMap}
                style={{
                    position: "absolute",
                    top: "10px",
                    right: "10px",
                    zIndex: 1000,
                    background: "black",
                    color: "white",
                    border: "none",
                    padding: "8px 12px",
                    borderRadius: "5px",
                    cursor: "pointer",
                }}
            >
                Reset Map
            </button>
        </div>
    );
};

export default MapComponent;