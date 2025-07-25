import React, { useEffect, useState } from "react";
import "./App.css";
import ChatBox from "./components/ChatBox";
import MapComponent from "./components/MapComponent";

function App() {
  const [query, setQuery] = useState("cafe");
  const [latitude, setLatitude] = useState(13.0067);
  const [longitude, setLongitude] = useState(80.2570);
  const [places, setPlaces] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);

  // Fetch user's current location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(pos.coords.latitude);
          setLongitude(pos.coords.longitude);
        },
        () => console.warn("Geolocation denied, using default location."),
        { enableHighAccuracy: true }
      );
    }
  }, []);

  return (
    <div className="App">
      {/* Title Section */}
      <h1 className="title">DeQue GeoFinder</h1>

      <div className="app-layout">
        {/* Map Component */}
        <div className="map-container">
          <MapComponent
            query={query}
            latitude={latitude}
            longitude={longitude}
            places={places}
            selectedPlace={selectedPlace}
          />
        </div>

        {/* ChatBox Component */}
        <div className="chat-container">
          <ChatBox
            latitude={latitude}
            longitude={longitude}
            onPlacesUpdate={(updatedPlaces) => {
              setPlaces(updatedPlaces);
              setQuery(updatedPlaces.length ? updatedPlaces[0].name : ""); // Sync query with first result
            }}
            onPlaceSelect={(place) => setSelectedPlace(place)}
          />
        </div>
      </div>
    </div>
  );
}

export default App;