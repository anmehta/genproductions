import FWCore.ParameterSet.Config as cms
import os

source = cms.Source("EmptySource")

generator = cms.EDFilter("SherpaGeneratorFilter",
  maxEventsToPrint = cms.int32(0),
  filterEfficiency = cms.untracked.double(1.0),
  crossSection = cms.untracked.double(-1),
  SherpaProcess = cms.string('ADDGravitonToDiPhoton_MS5500_NED4_KK1_M-200To500_13TeV-sherpa'),
  SherpackLocation = cms.string('slc6_amd64_gcc481/13TeV/sherpa/2.1.1/ADDGravToGG/v1/'),
  SherpackChecksum = cms.string('02d1ece89d9e350d9203332da65788dd'),
  FetchSherpack = cms.bool(True),
  SherpaPath = cms.string('./'),
  SherpaPathPiece = cms.string('./'),
  SherpaResultDir = cms.string('Result'),
  SherpaDefaultWeight = cms.double(1.0),
  SherpaParameters = cms.PSet(parameterSets = cms.vstring(
                             "MPI_Cross_Sections",
                             "Run"),
                              MPI_Cross_Sections = cms.vstring(
				" MPIs in Sherpa, Model = Amisic:",
				" semihard xsec = 74.9746 mb,",
				" non-diffractive xsec = 18.1593 mb with nd factor = 0.335."
                                                  ),
                              Run = cms.vstring(
				"(run){",
				" EVENTS = 100;",
				" EVENT_MODE = HepMC;",
				" WRITE_MAPPING_FILE 3;",
				"}(run)",
				"(beam){",
				" BEAM_1 = 2212; BEAM_ENERGY_1 = 6500.;",
				" BEAM_2 = 2212; BEAM_ENERGY_2 = 6500.;",
				"}(beam)",
				"(model){",
				" MODEL = ADD;",
				" M_S = 5500;",
				" N_ED = 4;",
				" KK_CONVENTION = 1;",
				" G_NEWTON = 6.707e-39;",
				"}(model)",
				"(processes){",
				" Process 21 21 -> 22 22;",
				" Scales VAR{Abs2(p[2]+p[3])};",
				" Loop_Generator gg_yy;",
				" End process;",
				" Process 93 93 -> 22 22;",
				" Order_EW 2;",
				" CKKW sqr(20./E_CMS);",
				" Print_Graphs : Process;",
				" End process;",
				"}(processes)",
				"(selector){",
				" Mass  22 22 200. 500.;",
				" PT 22 70. E_CMS;",
				" PseudoRapidity 22 -2.8 2.8;",
				"}(selector)",
				"(shower){",
				" CSS_EW_MODE = 1;",
				"}(shower)",
				"(integration){",
				" FINISH_OPTIMIZATION = Off;",
				"}(integration)",
				"(me){",
				" ME_SIGNAL_GENERATOR = Amegic;",
				"}(me)",
				"(mi){",
				" MI_HANDLER = Amisic;",
				"}(mi)"                                                  ),
                             )
)

ProductionFilterSequence = cms.Sequence(generator)

