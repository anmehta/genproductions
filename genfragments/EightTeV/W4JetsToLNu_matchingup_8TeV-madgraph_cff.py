import FWCore.ParameterSet.Config as cms

externalLHEProducer = cms.EDProducer('ExternalLHEProducer',
    scriptName = cms.FileInPath("GeneratorInterface/LHEInterface/data/run_madgraph_gridpack.sh"),
    outputFile = cms.string("W4JetsToLNu_matchingup_8TeV-madgraph_final.lhe"),
    numberOfParameters = cms.uint32(10),
    args = cms.vstring('slc5_ia32_gcc434/madgraph/V5_1.3.30/8TeV_Summer12/W4JetsToLNu_matchingup_8TeV-madgraph/v1',
    'W4JetsToLNu_matchingup_8TeV-madgraph','false','true','wjets','5','30','true','4','4'),
    nEvents = cms.uint32(50000)
)
