import { genkit, z } from "genkit";
import { googleAI } from "@genkit-ai/google-genai";

// Cloud Functions for Firebase supports Genkit natively. The onCallGenkit function creates a callable
// function from a Genkit action. It automatically implements streaming if your flow does.
// The https library also has other utility methods such as hasClaim, which verifies that
// a caller's token has a specific claim (optionally matching a specific value)
import { onCallGenkit, hasClaim } from "firebase-functions/https";

// Genkit will automatically look for the GOOGLE_GENAI_API_KEY environment
// variable in your .env file.

// The Firebase telemetry plugin exports a combination of metrics, traces, and logs to Google Cloud
// Observability. See https://firebase.google.com/docs/genkit/observability/telemetry-collection.
// import {enableFirebaseTelemetry} from "@genkit-ai/firebase";
// enableFirebaseTelemetry();

const ai = genkit({
  plugins: [
    // Load the Google AI provider (Gemini API).
    googleAI()
  ],
});

// Define a simple flow that prompts an LLM to generate menu suggestions.
const menuSuggestionFlow = ai.defineFlow({
  name: "Ecommerce-StoreSuggestionFlow",
  inputSchema: z.string().describe("An ecommerce perfumetheme").default("Perfumes"),
  outputSchema: z.string(),
  streamSchema: z.string(),
}, async (subject, { sendChunk }) => {
  // Construct a request and send it to the model API.
  const prompt =
    `Suggest an item for the menu of a ${subject} themed perfume ecommerce`;
  const { response, stream } = ai.generateStream({
    model: googleAI.model("gemini-1.5-flash"),
    prompt: prompt,
    config: {
      temperature: 1,
    },
  });

  for await (const chunk of stream) {
    sendChunk(chunk.text);
  }

  // Handle the response from the model API. In this sample, we just
  // convert it to a string, but more complicated flows might coerce the
  // response into structured output or chain the response into another
  // LLM call, etc.
  return (await response).text;
}
);

export const menuSuggestion = onCallGenkit({
  // Uncomment to enable AppCheck. This can reduce costs by ensuring only your Verified
  // app users can use your API. Read more at https://firebase.google.com/docs/app-check/cloud-functions
  // enforceAppCheck: true,

  // authPolicy can be any callback that accepts an AuthData (a uid and tokens dictionary) and the
  // request data. The isSignedIn() and hasClaim() helpers can be used to simplify. The following
  // will require the user to have the email_verified claim, for example.
  // authPolicy: hasClaim("email_verified"),

  // The function will automatically use the GOOGLE_GENAI_API_KEY
  // from your .env file or Cloud Secret Manager if configured.
}, menuSuggestionFlow);
