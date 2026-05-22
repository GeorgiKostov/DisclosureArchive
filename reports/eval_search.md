# Retrieval Evaluation Report

Generated: 2026-05-22T13:05:34+00:00
DB: `indexes\uap_release.sqlite`
Model: `BAAI/bge-small-en-v1.5`
Queries: 19

## Summary By Mode

| Mode | Passed | Failed | Avg best rank |
| --- | ---: | ---: | ---: |
| `keyword` | 18 | 1 | 1.17 |
| `vector` | 18 | 1 | 1.17 |
| `hybrid` | 19 | 0 | 1.32 |

## Hybrid Source Kinds

| Source kind | Hits |
| --- | ---: |
| `metadata` | 10 |
| `ocr_text` | 6 |
| `pdf_text` | 3 |

## Failure Highlights

_No hybrid failures._

## apollo17_grimaldi_flash

Query: `lunar surface flash Grimaldi`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 NASA-UAP-D2, Apollo 17 Transcript, 1972 (pdf_text p.16)<br>#2 NASA-UAP-D2, Apollo 17 Transcript, 1972 (metadata) |
| `vector` | yes | 1 | #1 NASA-UAP-D2, Apollo 17 Transcript, 1972 (pdf_text p.16)<br>#2 NASA-UAP-VM3, Apollo 12, 1969 (metadata)<br>#3 NASA-UAP-D6, Apollo 17 Technical Crew Debriefing, 1973 (metadata) |
| `hybrid` | yes | 1 | #1 NASA-UAP-D2, Apollo 17 Transcript, 1972 (pdf_text p.16)<br>#2 NASA-UAP-D2, Apollo 17 Transcript, 1972 (metadata)<br>#3 NASA-UAP-VM3, Apollo 12, 1969 (metadata) |

## usper_orb_formation

Query: `helicopter crew saw hot orange orbs split and flare in formation`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 3 | #1 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (metadata)<br>#2 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2)<br>#3 USPER Statement about UAP Sighting (pdf_text p.2) |
| `vector` | yes | 3 | #1 USPER Statement about UAP Sighting (pdf_text p.2)<br>#2 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2)<br>#3 USPER Statement about UAP Sighting (pdf_text p.2) |
| `hybrid` | yes | 3 | #1 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2)<br>#2 USPER Statement about UAP Sighting (pdf_text p.2)<br>#3 USPER Statement about UAP Sighting (pdf_text p.2) |

## gemini_bogey_transcript

Query: `Gemini bogey ten o'clock high unidentified object`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 255_t_763_r1b_transcripts (ocr_text p.1)<br>#2 255_t_763_r1b_transcripts (ocr_text p.1) |
| `vector` | yes | 1 | #1 NASA-UAP-D3, Gemini 7 Transcript, 1965 (pdf_text p.1)<br>#2 255_t_763_r1b_transcripts (ocr_text p.1)<br>#3 38_143685_box_Incident_Summaries_101-172 (ocr_text p.59) |
| `hybrid` | yes | 1 | #1 NASA-UAP-D3, Gemini 7 Transcript, 1965 (pdf_text p.1)<br>#2 255_t_763_r1b_transcripts (ocr_text p.1)<br>#3 255_t_763_r1b_transcripts (ocr_text p.1) |

## fbi_2023_fd302

Query: `Federal Bureau of Investigation date of entry September 2023`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 FBI September 2023 Sighting - Serial 5 (ocr_text p.1)<br>#2 FBI September 2023 Sighting - Serial 4 (ocr_text p.1)<br>#3 FBI September 2023 Sighting - Serial 3 (ocr_text p.1) |
| `vector` | yes | 1 | #1 FBI September 2023 Sighting - Serial 4 (ocr_text p.1)<br>#2 65_HS1-834228961_62-HQ-83894_Section_3 (ocr_text p.130)<br>#3 FBI September 2023 Sighting - Composite Sketch (metadata) |
| `hybrid` | yes | 1 | #1 FBI September 2023 Sighting - Serial 5 (ocr_text p.1)<br>#2 FBI September 2023 Sighting - Serial 4 (ocr_text p.1)<br>#3 65_HS1-834228961_62-HQ-83894_Section_3 (ocr_text p.130) |

## flying_discs_fsr_1949

Query: `flying discs flight service regulation 1949`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (metadata)<br>#2 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.65)<br>#3 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.58) |
| `vector` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (metadata)<br>#2 65_HS1-834228961_62-HQ-83894_Section_7 (ocr_text p.43)<br>#3 65_HS1-834228961_62-HQ-83894_Section_4 (ocr_text p.169) |
| `hybrid` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (metadata)<br>#2 65_HS1-834228961_62-HQ-83894_Section_7 (ocr_text p.43)<br>#3 65_HS1-834228961_62-HQ-83894_Section_4 (ocr_text p.169) |

## project_blue_book_termination

Query: `termination of Project Blue Book Air Force regulation establishing controlling`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177)<br>#2 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177) |
| `vector` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177)<br>#2 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177)<br>#3 65_HS1-834228961_62-HQ-83894_Section_5 (ocr_text p.75) |
| `hybrid` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177)<br>#2 65_HS1-834228961_62-HQ-83894_Section_10 (ocr_text p.177)<br>#3 65_HS1-834228961_62-HQ-83894_Section_5 (ocr_text p.75) |

## af_form_112_director_intelligence

Query: `AF Form 112 forwarded Director of Intelligence Headquarters United States Air Force`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.3)<br>#2 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.67)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.11) |
| `vector` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.3)<br>#2 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.67)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.11) |
| `hybrid` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.3)<br>#2 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.67)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_164 (ocr_text p.11) |

## bethel_caa_aircraft_vicinity

Query: `Bethel Civil Aeronautics Administration station aircraft in the vicinity`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | no |  | #1 65_HS1-834228961_62-HQ-83894_Section_4 (ocr_text p.5)<br>#2 65_HS1-834228961_62-HQ-83894_Section_4 (ocr_text p.5)<br>#3 65_HS1-834228961_62-HQ-83894_Section_7 (ocr_text p.46) |
| `vector` | yes | 1 | #1 38_143685_box7_Incident_Summaries_1-100 (ocr_text p.125)<br>#2 65_HS1-834228961_62-HQ-83894_Section_2 (ocr_text p.183)<br>#3 38_143685_box7_Incident_Summaries_1-100 (ocr_text p.73) |
| `hybrid` | yes | 2 | #1 65_HS1-834228961_62-HQ-83894_Section_4 (ocr_text p.5)<br>#2 38_143685_box7_Incident_Summaries_1-100 (ocr_text p.125)<br>#3 65_HS1-834228961_62-HQ-83894_Section_2 (ocr_text p.183) |

## new_haven_flying_saucers

Query: `New Haven flying saucers July 18 1947 office memorandum`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 65_HS1-834228961_62-HQ-83894_Section_1 (ocr_text p.103)<br>#2 65_HS1-834228961_62-HQ-83894_Section_1 (ocr_text p.169)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_130 (ocr_text p.65) |
| `vector` | no |  | #1 65_HS1-834228961_62-HQ-83894_Section_3 (ocr_text p.169)<br>#2 65_HS1-834228961_62-HQ-83894_Section_1 (ocr_text p.165)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_130 (ocr_text p.63) |
| `hybrid` | yes | 4 | #1 65_HS1-834228961_62-HQ-83894_Serial_130 (ocr_text p.65)<br>#2 65_HS1-834228961_62-HQ-83894_Section_3 (ocr_text p.169)<br>#3 65_HS1-834228961_62-HQ-83894_Section_1 (ocr_text p.165) |

## hickam_cardboard_cane_fields

Query: `Hickam flying disc cardboard metallic substance funneled air currents cane fields`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.91) |
| `vector` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.91)<br>#2 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.92)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_130 (ocr_text p.14) |
| `hybrid` | yes | 1 | #1 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.91)<br>#2 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.92)<br>#3 65_HS1-834228961_62-HQ-83894_Serial_130 (ocr_text p.14) |

## vandenberg_launch_summary

Query: `Launch Summary Vandenberg AFB 2000`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (metadata)<br>#2 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.3)<br>#3 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.108) |
| `vector` | yes | 1 | #1 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (metadata)<br>#2 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.3)<br>#3 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.11) |
| `hybrid` | yes | 1 | #1 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (metadata)<br>#2 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.3)<br>#3 DOW-UAP-D49, Launch Summary, Vandenberg AFB, 2000 (pdf_text p.11) |

## persian_gulf_august_2020

Query: `mission report Persian Gulf August 2020`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 DOW-UAP-D60, Mission Report, Persian Gulf, August 2020 (metadata)<br>#2 DOW-UAP-D61, Mission Report, Persian Gulf, August 2020 (metadata)<br>#3 DOW-UAP-D60, Mission Report, Persian Gulf, August 2020 (ocr_text p.3) |
| `vector` | yes | 2 | #1 DOW-UAP-D65, Mission Report, Persian Gulf, July 2020 (metadata)<br>#2 DOW-UAP-D61, Mission Report, Persian Gulf, August 2020 (metadata)<br>#3 DOW-UAP-D60, Mission Report, Persian Gulf, August 2020 (metadata) |
| `hybrid` | yes | 1 | #1 DOW-UAP-D60, Mission Report, Persian Gulf, August 2020 (metadata)<br>#2 DOW-UAP-D61, Mission Report, Persian Gulf, August 2020 (metadata)<br>#3 DOW-UAP-D65, Mission Report, Persian Gulf, July 2020 (metadata) |

## skylab_technical_debriefing

Query: `Skylab technical crew debriefing 1973`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 NASA-UAP-D7, Skylab Techincal Crew Debriefing 1973 (metadata)<br>#2 NASA-UAP-D7, Skylab Techincal Crew Debriefing 1973 (ocr_text p.9) |
| `vector` | yes | 1 | #1 NASA-UAP-D7, Skylab Techincal Crew Debriefing 1973 (metadata)<br>#2 255-t-763-r1b-excerpt (video_metadata)<br>#3 255-t-763-r1b-excerpt (metadata) |
| `hybrid` | yes | 1 | #1 NASA-UAP-D7, Skylab Techincal Crew Debriefing 1973 (metadata)<br>#2 NASA-UAP-D7, Skylab Techincal Crew Debriefing 1973 (ocr_text p.9)<br>#3 255-t-763-r1b-excerpt (video_metadata) |

## western_us_fbi_photos

Query: `FBI photo western United States late 2025`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 FBI Photo B17 (metadata)<br>#2 FBI Photo B24 (metadata)<br>#3 FBI Photo B16 (metadata) |
| `vector` | yes | 1 | #1 FBI Photo B5 (metadata)<br>#2 FBI Photo B15 (metadata)<br>#3 FBI Photo B22 (metadata) |
| `hybrid` | yes | 1 | #1 FBI Photo B17 (metadata)<br>#2 FBI Photo B24 (metadata)<br>#3 FBI Photo B16 (metadata) |

## unresolved_uap_kuwait

Query: `unresolved UAP report Kuwait May 2022 Iraq`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 2 | #1 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (pdf_text p.1)<br>#2 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (ocr_text p.1)<br>#3 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (metadata) |
| `vector` | yes | 1 | #1 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (metadata)<br>#2 DOW-UAP-PR21, Unresolved UAP Report, Iraq, May 2022 (metadata)<br>#3 DOW-UAP-D23, Mission Report, United Arab Emirates, October 2023 (video_metadata) |
| `hybrid` | yes | 1 | #1 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (metadata)<br>#2 DOW-UAP-PR20, Unresolved UAP Report, Kuwait, May 2022 (pdf_text p.1)<br>#3 DOW-UAP-PR21, Unresolved UAP Report, Iraq, May 2022 (metadata) |

## sandia_green_fireballs

Query: `green fireballs over New Mexico atomic installations 1949`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (metadata)<br>#2 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (pdf_text p.21)<br>#3 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (pdf_text p.70) |
| `vector` | yes | 1 | #1 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (metadata)<br>#2 65_HS1-834228961_62-HQ-83894_Section_6 (ocr_text p.5)<br>#3 65_HS1-834228961_62-HQ-83894_Section_6 (ocr_text p.25) |
| `hybrid` | yes | 1 | #1 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (metadata)<br>#2 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (pdf_text p.21)<br>#3 Sandia Base Correspondence - New Mexico Aerial Phenomena and Green Fireballs (1948-1949) (pdf_text p.21) |

## sary_shagan_green_object

Query: `bright green concentric circles unidentified object Soviet weapons range`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 CIA Intelligence Information Report - Sary Shagan, USSR (1973) (metadata)<br>#2 CIA Intelligence Information Report - Sary Shagan, USSR (1973) (pdf_text p.3)<br>#3 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.80) |
| `vector` | yes | 1 | #1 CIA Intelligence Information Report - Sary Shagan, USSR (1973) (pdf_text p.3)<br>#2 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.80)<br>#3 38_143685_box_Incident_Summaries_173-233 (ocr_text p.128) |
| `hybrid` | yes | 1 | #1 CIA Intelligence Information Report - Sary Shagan, USSR (1973) (metadata)<br>#2 CIA Intelligence Information Report - Sary Shagan, USSR (1973) (pdf_text p.3)<br>#3 342_HS1-416511228_319.1 Flying Discs 1949 (ocr_text p.80) |

## odni_usper_orb_t_formation

Query: `senior intelligence officer helicopter orange orbs T formation chasing fighter jets`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (metadata)<br>#2 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2)<br>#3 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2) |
| `vector` | yes | 1 | #1 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (metadata)<br>#2 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.1)<br>#3 DOW-UAP-D51, Email Correspondence, Pacific Time Zone, March 2023 (pdf_text p.4) |
| `hybrid` | yes | 1 | #1 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (metadata)<br>#2 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2)<br>#3 ODNI USPER Narrative - Senior Intelligence Officer Orb Encounter (2025) (pdf_text p.2) |

## pajarito_astronomers_ufo_talk

Query: `Los Alamos astronomers club why should a scientist be concerned about UFOs`

| Mode | Pass | Best rank | Top results |
| --- | --- | ---: | --- |
| `keyword` | yes | 1 | #1 Pajarito Astronomers - Why Should a Scientist Be Concerned About UFOs (1986) (metadata)<br>#2 Pajarito Astronomers - Why Should a Scientist Be Concerned About UFOs (1986) (pdf_text p.1)<br>#3 255_413270_UFO's_and_Defense_What_Should_we_Prepare_For (ocr_text p.91) |
| `vector` | yes | 1 | #1 Pajarito Astronomers - Why Should a Scientist Be Concerned About UFOs (1986) (metadata)<br>#2 255_413270_UFO's_and_Defense_What_Should_we_Prepare_For (ocr_text p.8)<br>#3 255_413270_UFO's_and_Defense_What_Should_we_Prepare_For (ocr_text p.67) |
| `hybrid` | yes | 1 | #1 Pajarito Astronomers - Why Should a Scientist Be Concerned About UFOs (1986) (metadata)<br>#2 Pajarito Astronomers - Why Should a Scientist Be Concerned About UFOs (1986) (pdf_text p.1)<br>#3 255_413270_UFO's_and_Defense_What_Should_we_Prepare_For (ocr_text p.8) |
