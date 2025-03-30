"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

export default function SuccessPage() {
  const router = useRouter();
  const [fadeIn, setFadeIn] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setFadeIn(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleSubmitAnother = useCallback(async () => {
    try {
      const response = await fetch("${process.env.NEXT_PUBLIC_API_URL}/close-connection", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        console.error("Failed to call /close-connection");
      }

      localStorage.removeItem("formdata");

      if (localStorage.getItem("formdata") !== null) {
        console.warn("formdata was not removed from localStorage!");
      }

      router.push("/");
    } catch (error) {
      console.error("Error during submission cleanup:", error);
    }
  }, [router]);

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 p-6">
      <div
        className={`bg-white shadow-2xl rounded-2xl px-10 py-12 text-center max-w-lg w-full transform transition-opacity duration-700 ${
          fadeIn ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
        }`}
      >
        {/* Animated Checkmark */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-4xl shadow-inner animate-bounce-slow">
            ✅
          </div>
        </div>

        {/* Success Message */}
        <h1 className="text-4xl font-bold text-blue-700 mb-3">
          Success!
        </h1>
        <p className="text-md text-gray-600 mb-8">
          Your form has been submitted successfully.
        </p>

        {/* Action Button */}
        <div className="flex justify-center">
          <button
            onClick={handleSubmitAnother}
            className="bg-blue-600 text-white px-8 py-3 text-lg font-medium rounded-xl shadow-lg hover:bg-blue-700 transition duration-300"
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
