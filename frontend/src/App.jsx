import { useEffect, useState } from "react";
import API from "./services/api";

function App() {

    const [message, setMessage] = useState("Connecting to backend...");
    const [error, setError] = useState("");

    useEffect(() => {

        API.get("/")
            .then((response) => {

                console.log("Backend response:", response.data);

                setMessage(response.data.message);
                setError("");
            })
            .catch((error) => {

                console.error("Backend connection error:", error);

                setMessage("");
                setError("Backend connection failed");
            });

    }, []);

    return (
        <div>
            <h1>Study Shuttle System</h1>

            {message && (
                <p>{message}</p>
            )}

            {error && (
                <p>{error}</p>
            )}
        </div>
    );
}

export default App;