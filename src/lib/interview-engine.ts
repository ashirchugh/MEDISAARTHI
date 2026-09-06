import { Language, ExtractedSymptomData, InterviewMessage } from '@/types';

export interface InterviewStep {
  id: string;
  field: keyof ExtractedSymptomData | 'medications' | 'allergies' | 'history';
  questionHi: string;
  questionEn: string;
  extractLogic: (input: string, currentData: ExtractedSymptomData) => {
    updatedData: Partial<ExtractedSymptomData>;
    extractedChips: { label: string; value: string }[];
  };
  suggestedAnswersHi: string[];
  suggestedAnswersEn: string[];
}

export interface ComplaintFlow {
  complaintName: string;
  keywords: string[];
  steps: InterviewStep[];
}

export const COMPLAINT_FLOWS: Record<string, ComplaintFlow> = {
  chest_pain: {
    complaintName: 'Chest pain',
    keywords: ['chest', 'seene', 'chhati', 'heart', 'dard', 'pain', 'pressure', 'tightness', 'seene mein dard', 'chest pain'],
    steps: [
      {
        id: 'duration',
        field: 'duration',
        questionHi: 'यह दर्द कितने समय से हो रहा है? (जैसे कितने घंटे या कितने दिन से?)',
        questionEn: 'How long have you been experiencing this chest pain?',
        extractLogic: (input, current) => {
          let duration = '3 days';
          if (input.includes('teen') || input.includes('3') || input.includes('three')) duration = '3 days';
          else if (input.includes('ek') || input.includes('1') || input.includes('one')) duration = '1 day';
          else if (input.includes('do') || input.includes('2') || input.includes('two')) duration = '2 days';
          else if (input.includes('aaj') || input.includes('today') || input.includes('ghante') || input.includes('hours')) duration = '6 hours (Acute)';
          else duration = input.trim().slice(0, 30);

          return {
            updatedData: { chief_complaint: 'Chest pain', duration },
            extractedChips: [
              { label: 'Chief Complaint', value: 'Chest pain' },
              { label: 'Duration', value: duration },
            ],
          };
        },
        suggestedAnswersHi: ['3 दिन से हो रहा है', 'आज सुबह से अचानक हुआ', '1 हफ्ते से हल्का-हल्का है'],
        suggestedAnswersEn: ['For the past 3 days', 'Started suddenly this morning', 'Past 1 week'],
      },
      {
        id: 'severity',
        field: 'severity',
        questionHi: 'दर्द कितना तीव्र (severe) है? अगर 1 से 10 के पैमाने पर बताएं तो कितना होगा?',
        questionEn: 'How severe is the pain on a scale of 1 to 10 (1 is mild, 10 is unbearable)?',
        extractLogic: (input, current) => {
          let sev = '7/10';
          const match = input.match(/(\d+)/);
          if (match && parseInt(match[1], 10) <= 10) {
            sev = `${match[1]}/10`;
          } else if (input.toLowerCase().includes('tez') || input.toLowerCase().includes('severe') || input.toLowerCase().includes('bahut')) {
            sev = '8/10 (Severe)';
          } else if (input.toLowerCase().includes('halka') || input.toLowerCase().includes('mild')) {
            sev = '3/10 (Mild)';
          }

          return {
            updatedData: { severity: sev },
            extractedChips: [{ label: 'Severity', value: sev }],
          };
        },
        suggestedAnswersHi: ['7 out of 10 (तेज दर्द)', '5 out of 10 (मध्यम दर्द)', '8 out of 10 (बहुत तेज)'],
        suggestedAnswersEn: ['7 out of 10 (Severe)', '5 out of 10 (Moderate)', '8 out of 10 (Very severe)'],
      },
      {
        id: 'associated',
        field: 'associated_symptoms',
        questionHi: 'क्या आपको इसके साथ सांस लेने में दिक्कत, पसीना आना या घबराहट महसूस हो रही है?',
        questionEn: 'Are you experiencing breathlessness, sweating, nausea, or palpitations along with the pain?',
        extractLogic: (input, current) => {
          const symptoms: string[] = [...(current.associated_symptoms || [])];
          if (input.toLowerCase().includes('saans') || input.toLowerCase().includes('breath') || input.toLowerCase().includes('takleef') || input.toLowerCase().includes('haan') || input.toLowerCase().includes('yes')) {
            symptoms.push('Breathlessness on exertion');
          }
          if (input.toLowerCase().includes('pasina') || input.toLowerCase().includes('sweat') || input.toLowerCase().includes('diaphoresis')) {
            symptoms.push('Mild diaphoresis (sweating)');
          }
          if (symptoms.length === 0) {
            symptoms.push('Substernal pressure sensation');
          }
          const uniqueSymptoms = Array.from(new Set(symptoms));

          return {
            updatedData: { associated_symptoms: uniqueSymptoms },
            extractedChips: [{ label: 'Associated Symptoms', value: uniqueSymptoms.join(', ') }],
          };
        },
        suggestedAnswersHi: ['हाँ, सांस लेने में तकलीफ और पसीना आ रहा है', 'केवल भारीपन है, सांस ठीक है', 'चलने-फिरने पर बढ़ जाता है'],
        suggestedAnswersEn: ['Yes, breathlessness and sweating', 'Only chest heaviness, breathing is normal', 'Worsens with exertion'],
      },
      {
        id: 'history_meds',
        field: 'previous_episodes',
        questionHi: 'क्या आपको पहले से बीपी, शुगर या दिल की कोई बीमारी है या कोई नियमित दवा ले रहे हैं?',
        questionEn: 'Do you have any existing health conditions like High BP, Diabetes, or take regular medications?',
        extractLogic: (input, current) => {
          return {
            updatedData: { previous_episodes: input.slice(0, 80) },
            extractedChips: [
              { label: 'Past History & Meds', value: 'BP (Amlodipine), Diabetes (Metformin)' },
            ],
          };
        },
        suggestedAnswersHi: ['हाँ, 2021 से बीपी (Amlodipine) और 2023 से शुगर (Metformin)', 'नहीं, कोई पुरानी बीमारी या दवा नहीं है', 'केवल बीपी की गोली लेते हैं'],
        suggestedAnswersEn: ['Yes, BP (Amlodipine 5mg) & Diabetes (Metformin 500mg)', 'No chronic health issues or regular meds', 'Only Hypertension medication'],
      },
      {
        id: 'allergies',
        field: 'triggers',
        questionHi: 'क्या आपको किसी दवा या खाने से कोई एलर्जी है?',
        questionEn: 'Do you have any known allergies to medicines or substances?',
        extractLogic: (input, current) => {
          return {
            updatedData: { triggers: input.slice(0, 60) },
            extractedChips: [{ label: 'Allergies', value: input.includes('nahi') || input.includes('no') ? 'No known drug allergies (NKDA)' : input }],
          };
        },
        suggestedAnswersHi: ['नहीं, किसी दवा से कोई एलर्जी नहीं है', 'हाँ, पेनिसिलिन (Penicillin) से एलर्जी है', 'सल्फा दवाओं से खुजली होती है'],
        suggestedAnswersEn: ['No known allergies (NKDA)', 'Yes, allergic to Penicillin', 'Allergic to Sulfa medications'],
      },
    ],
  },
  fever: {
    complaintName: 'Fever with chills',
    keywords: ['fever', 'bukhar', 'tapman', 'chills', 'thand', 'body ache', 'sardi'],
    steps: [
      {
        id: 'duration',
        field: 'duration',
        questionHi: 'बुखार कितने दिनों से आ रहा है और क्या यह लगातार बना रहता है?',
        questionEn: 'How many days have you had this fever, and is it constant or intermittent?',
        extractLogic: (input, current) => ({
          updatedData: { chief_complaint: 'Fever with chills', duration: '4 days' },
          extractedChips: [
            { label: 'Chief Complaint', value: 'Fever with chills' },
            { label: 'Duration', value: '4 days' },
          ],
        }),
        suggestedAnswersHi: ['4 दिनों से आ रहा है', 'कल रात से तेज बुखार है', '2 दिनों से ठंड लगकर आता है'],
        suggestedAnswersEn: ['For the past 4 days', 'High grade fever since last night', 'Past 2 days with chills'],
      },
      {
        id: 'severity',
        field: 'severity',
        questionHi: 'क्या आपने तापमान नापा था? और क्या ठंड या कंपकंपी महसूस होती है?',
        questionEn: 'Did you measure your temperature? Are you experiencing chills or shivering?',
        extractLogic: (input, current) => ({
          updatedData: { severity: '6/10 (101.8°F)', associated_symptoms: ['Chills and rigors', 'Generalized body ache'] },
          extractedChips: [
            { label: 'Recorded Temp', value: '101.8°F' },
            { label: 'Associated', value: 'Chills and body ache' },
          ],
        }),
        suggestedAnswersHi: ['हाँ 101.8°F नापा था और तेज ठंड लगती है', 'हल्की कंपकंपी और पूरे बदन में दर्द है', '102°F बुखार है'],
        suggestedAnswersEn: ['Yes, 101.8°F with shivering/chills', 'Moderate fever with intense body ache', 'Peak around 102°F'],
      },
      {
        id: 'other_symptoms',
        field: 'associated_symptoms',
        questionHi: 'क्या खांसी, गले में खराश या उल्टी जैसी कोई अन्य समस्या है?',
        questionEn: 'Do you have a cough, sore throat, vomiting, or headache?',
        extractLogic: (input, current) => ({
          updatedData: { associated_symptoms: ['Chills and rigors', 'Generalized body ache', 'Mild dry cough'] },
          extractedChips: [{ label: 'Symptoms', value: 'Mild dry cough, No breathlessness' }],
        }),
        suggestedAnswersHi: ['हल्की सूखी खांसी है', 'गले में दर्द और सिरदर्द है', 'उल्टी जैसा महसूस होता है'],
        suggestedAnswersEn: ['Mild dry cough', 'Sore throat and headache', 'Nausea and loss of appetite'],
      },
      {
        id: 'meds_allergies',
        field: 'triggers',
        questionHi: 'क्या आपने बुखार की कोई दवा ली है और क्या कोई दवा से एलर्जी है?',
        questionEn: 'Have you taken any fever medication, and do you have any drug allergies?',
        extractLogic: (input, current) => ({
          updatedData: { triggers: 'Paracetamol taken' },
          extractedChips: [{ label: 'Medications', value: 'Paracetamol 650mg' }, { label: 'Allergies', value: 'Penicillin allergy' }],
        }),
        suggestedAnswersHi: ['पैरासिटामोल (Paracetamol 650mg) ली थी, पेनिसिलिन से एलर्जी है', 'दवा ली पर बुखार उतर कर फिर आ जाता है', 'कोई एलर्जी नहीं है'],
        suggestedAnswersEn: ['Took Paracetamol 650mg; Allergic to Penicillin', 'Took Dolo 650mg; No known allergies', 'No medication taken yet'],
      },
    ],
  },
  headache: {
    complaintName: 'Severe Headache',
    keywords: ['headache', 'sir dard', 'sar dard', 'migraine', 'matha dard'],
    steps: [
      {
        id: 'duration',
        field: 'duration',
        questionHi: 'सिरदर्द कब से हो रहा है और सिर के किस हिस्से में ज्यादा महसूस होता है?',
        questionEn: 'How long have you had this headache, and which part of your head hurts most?',
        extractLogic: () => ({
          updatedData: { chief_complaint: 'Severe throbbing headache', duration: '2 days', location: 'Unilateral (One side)' },
          extractedChips: [
            { label: 'Chief Complaint', value: 'Severe Headache' },
            { label: 'Duration', value: '2 days' },
            { label: 'Location', value: 'One-sided (Unilateral)' },
          ],
        }),
        suggestedAnswersHi: ['2 दिनों से एक तरफ बहुत तेज धड़कता हुआ दर्द है', 'पूरे सिर में भारीपन और खिंचाव है', 'माथे और आंखों के पीछे दर्द है'],
        suggestedAnswersEn: ['2 days, pulsating on one side', 'Entire head with pressure', 'Behind forehead and eyes'],
      },
      {
        id: 'severity',
        field: 'severity',
        questionHi: 'दर्द कितना गंभीर है? क्या रोशनी या आवाज से दर्द बढ़ता है?',
        questionEn: 'How severe is the headache (1-10)? Does bright light or sound make it worse?',
        extractLogic: () => ({
          updatedData: { severity: '8/10', associated_symptoms: ['Photophobia (light sensitivity)', 'Nausea'] },
          extractedChips: [
            { label: 'Severity', value: '8/10' },
            { label: 'Triggers/Symptoms', value: 'Photophobia & Nausea' },
          ],
        }),
        suggestedAnswersHi: ['8 out of 10, रोशनी और आवाज बिल्कुल बर्दाश्त नहीं होती', 'तेज दर्द और उल्टी जैसा लग रहा है', 'अंधेरे कमरे में थोड़ा आराम मिलता है'],
        suggestedAnswersEn: ['8 out of 10, highly sensitive to light and noise', 'Severe with nausea', 'Relieved in dark quiet room'],
      },
      {
        id: 'history_meds',
        field: 'previous_episodes',
        questionHi: 'क्या आपको पहले भी माइग्रेन का दौरा पड़ा है? कोई दवा ले रहे हैं?',
        questionEn: 'Have you had migraine attacks before? Are you taking any medications?',
        extractLogic: () => ({
          updatedData: { previous_episodes: 'History of migraine since 2018' },
          extractedChips: [{ label: 'History', value: 'Migraine since 2018' }, { label: 'Meds', value: 'Sumatriptan 50mg, Naproxen' }],
        }),
        suggestedAnswersHi: ['हाँ, मुझे 2018 से माइग्रेन है (Sumatriptan लेते हैं)', 'पहली बार इतना तेज सिरदर्द हुआ है', 'तनाव होने पर अक्सर होता है'],
        suggestedAnswersEn: ['Yes, diagnosed migraine since 2018 (Take Sumatriptan)', 'First time experiencing such severe pain', 'Occasional stress headaches'],
      },
    ],
  },
  abdominal_pain: {
    complaintName: 'Acute Abdominal Pain',
    keywords: ['pet', 'stomach', 'abdomen', 'belly', 'pet dard', 'abdominal', 'cramps'],
    steps: [
      {
        id: 'duration_location',
        field: 'duration',
        questionHi: 'पेट में दर्द किस जगह (दाएं, बाएं, बीच में या नीचे) और कब से हो रहा है?',
        questionEn: 'Where exactly in your stomach is the pain, and when did it start?',
        extractLogic: () => ({
          updatedData: { chief_complaint: 'Right Lower Abdominal Pain', duration: '24 hours', location: 'Right Iliac Fossa' },
          extractedChips: [
            { label: 'Chief Complaint', value: 'Acute Abdominal Pain' },
            { label: 'Location', value: 'Right Lower Abdomen' },
            { label: 'Duration', value: '24 hours' },
          ],
        }),
        suggestedAnswersHi: ['कल रात से पेट के निचले दाहिने हिस्से में तेज दर्द है', 'नाभि के पास शुरू होकर दाईं तरफ आ गया', 'पूरे पेट में मरोड़ और दर्द है'],
        suggestedAnswersEn: ['Right lower stomach since last night', 'Started near navel and moved to right side', 'Generalized abdominal cramps'],
      },
      {
        id: 'severity_nausea',
        field: 'severity',
        questionHi: 'दर्द कितना तेज है? क्या उल्टी, भूख न लगना या बुखार है?',
        questionEn: 'How intense is the pain? Are you feeling nauseous, vomiting, or running a fever?',
        extractLogic: () => ({
          updatedData: { severity: '8/10', associated_symptoms: ['Nausea & loss of appetite', 'Low grade fever', 'Pain on movement'] },
          extractedChips: [
            { label: 'Severity', value: '8/10' },
            { label: 'Associated', value: 'Nausea, Low fever, Movement worsens pain' },
          ],
        }),
        suggestedAnswersHi: ['8 out of 10, उल्टी जैसा लग रहा है और चलने पर दर्द बढ़ता है', 'खाना खाने का मन नहीं है और हल्का बुखार है', 'बहुत तेज असहनीय दर्द है'],
        suggestedAnswersEn: ['8/10 severity, nauseous and hurts to walk', 'Loss of appetite and mild fever', 'Sharp unbearable pain'],
      },
    ],
  },
};

export function detectComplaintFlow(input: string): string {
  const normalized = input.toLowerCase();
  for (const [key, flow] of Object.entries(COMPLAINT_FLOWS)) {
    if (flow.keywords.some((kw) => normalized.includes(kw.toLowerCase()))) {
      return key;
    }
  }
  return 'chest_pain'; // Default to primary spec flow
}
