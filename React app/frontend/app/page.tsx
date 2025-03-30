"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2 } from "lucide-react"; // Optional: Loading spinner icon if using Lucide

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleOpenForm = async () => {
    setLoading(true);

    try {
      const openFormResponse = await fetch('${process.env.NEXT_PUBLIC_API_URL}/api/open-form', {
        method: 'POST',
      });

      if (!openFormResponse.ok) {
        console.error('❌ Error opening database connection');
        return;
      }

      console.log("✅ Form opened successfully, now reserving Job ID...");

      const reserveJobResponse = await fetch('${process.env.NEXT_PUBLIC_API_URL}/api/reserve-job', {
        method: 'POST',
      });

      if (!reserveJobResponse.ok) {
        console.error('❌ Error reserving Job ID');
        return;
      }

      const { jobID } = await reserveJobResponse.json();
      console.log(`✅ Job ID ${jobID} reserved`);

      router.push(`/Form?jobID=${jobID}`);
    } catch (error) {
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 p-6">
      <div className="bg-white shadow-2xl rounded-2xl px-10 py-12 text-center max-w-lg w-full">
        {/* Company Branding */}
        <h1 className="text-5xl font-black text-blue-800 mb-3">
          Business name
        </h1>
        <p className="text-md text-gray-500 mb-8 italic">
          Tech Repair Made Simple.
        </p>

        {/* Welcome Message */}
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
          Welcome!
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Need help with your device? Start a new service form below.
        </p>

        {/* Action Button */}
        <div className="flex justify-center">
        <button
          onClick={handleOpenForm}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl shadow-lg hover:bg-blue-700 transition duration-300 disabled:opacity-60 disabled:cursor-not-allowed flex items-center"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin w-5 h-5 mr-2" />
              Preparing Form...
            </>
          ) : (
            <>
              🛠️ Start Booking
            </>
          )}
        </button>
      </div>

      </div>
    </div>
  );
}
