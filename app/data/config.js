(function () {
  'use strict';
  window.PHV_CONFIG = {
    version: '1.0.0', passPercent: 60,
    handbookUrl: 'https://content.tfl.gov.uk/phv-driver-handbook-v1.pdf',
    presets: {
      A: { name: 'Preset A · 37 questions / 45 minutes', minutes:45, mcq:18, cloze:17, reading:2, status:'Reported format; exact current composition is not confirmed by TfL.' },
      B: { name: 'Preset B · 36 questions / 60 minutes', minutes:60, mcq:22, cloze:12, reading:2, status:'Unverified alternative based on third-party reports.' }
    },
    topo: {minutes:70, routes:{short:1,closure:1,long:1}, mcqCount:21, mcqMarks:34, routeMarks:22, totalMarks:100, status:'TfL confirms 24 questions, 70 minutes, 100 marks (66 routes + 34 other questions), and a 60% pass mark. Equal route weights and the per-section mix are simulator defaults.'},
    marking: {endpointTolerance:40, corridor:25, referenceTolerance:3, endpointDeduction:3, illegalDeduction:4, offroadDeduction:4, directness:[[1.05,0],[1.15,3],[1.30,7],[Infinity,12]]},
    defaults: {candidate:'Candidate',preset:'A',blankStyle:'drag',drawingMode:'real',practiceTimer:false,partialCredit:true,clozeBlocking:true},
    seruSections: ['London PHV Driver Licensing','Licensing Requirements for PHVs','Carrying out Private Hire Journeys','Staying Safe','Driver Behaviour','Driving and Parking in London','Safer Driving','Being Aware of Equality and Disability','Safeguarding Children and Adults at Risk','Ridesharing']
  };
}());
