# Research calibration and evidence map — V4.0 (2025 one-year release)

This release is **synthetic**. It combines evidence-backed calendar/climate anchors with transparent scenario coefficients. An external source supporting a phenomenon does **not** mean every numerical multiplier in the simulator was measured in that source.

## Evidence-backed anchors used directly

1. **Ramadan 2025 began on 2 March in Bangladesh.**
   - Bangladesh Sangbad Sangstha (BSS), 1 March 2025: National Moon Sighting Committee announcement.
   - https://www.bssnews.net/bangla/national/182107

2. **Eid-ul-Fitr 2025 and extended government closure.**
   - The official 2025 holiday schedule listed the Eid break around 29 March–2 April; the Ministry of Public Administration subsequently declared 3 April an additional executive-order holiday.
   - https://mopa.gov.bd/pages/notices/69413993a31054345f0e5f42
   - Bangladesh Bank holiday circular (derived from MoPA notification): https://www.bb.org.bd/mediaroom/circulars/dos/nov172024dosl26e.pdf

3. **Eid-ul-Adha fell on 7 June 2025 in Bangladesh.**
   - Islamic Foundation / National Moon Sighting Committee announcement.
   - https://islamicfoundation.gov.bd/site/notices/2f970be8-56bf-4ec4-9b1a-0c85801b2318/

4. **Eid-ul-Adha government closure was extended through 11–12 June; 17 and 24 May were declared working Saturdays.**
   - Ministry of Public Administration notice, 7 May 2025.
   - https://mopa.gov.bd/pages/notices/69413992a31054345f0e5ef7

5. **Eid-e-Milad-un-Nabi public holiday was rescheduled to 6 September 2025.**
   - Ministry of Public Administration notice, 28 August 2025.
   - https://mopa.gov.bd/pages/public-holiday/%E0%A6%AA%E0%A6%AC%E0%A6%BF%E0%A6%A4%E0%A7%8D%E0%A6%B0-%E0%A6%88%E0%A6%A6-%E0%A6%87-%E0%A6%AE%E0%A6%BF%E0%A6%B2%E0%A6%BE%E0%A6%A6%E0%A7%81%E0%A6%A8%E0%A7%8D%E0%A6%A8%E0%A6%AC%E0%A7%80-%E0%A6%B8%E0%A6%BE-%E0%A6%89%E0%A6%AA%E0%A6%B2%E0%A6%95%E0%A7%8D%E0%A6%B7%E0%A7%8D%E0%A6%AF%E0%A7%87-%E0%A6%B8%E0%A6%BE%E0%A6%A7%E0%A6%BE%E0%A6%B0%E0%A6%A3-%E0%A6%9B%E0%A7%81%E0%A6%9F%E0%A6%BF%E0%A6%B0-%E0%A6%A8%E0%A6%BF%E0%A6%B0%E0%A7%8D%E0%A6%A7%E0%A6%BE%E0%A6%B0%E0%A6%BF%E0%A6%A4-1638d3-694139b2a31054345f0e6348

6. **Secondary-school 2025 long breaks.**
   - Published education-calendar reporting states Ramadan-related closure beginning 2 March with classes resuming 8 April; Eid-ul-Adha/summer break 1–19 June; Durga Puja break 28 September–7 October.
   - https://www.prothomalo.com/education/higher-education/fe9jjmo9c9

7. **Government Ramadan office hours were shortened to 09:00–15:30.**
   - Ministry of Public Administration notice / contemporary reporting.
   - https://mopa.gov.bd/pages/notices/69413993a31054345f0e5fcc

8. **Dhaka monthly temperature and precipitation seasonality.**
   - Tokyo Climate Center / Japan Meteorological Agency ClimatView monthly normals for Dhaka (station 41923): monthly mean temperature and precipitation.
   - https://www.data.jma.go.jp/tcc/tcc/products/climate/climatview/graph_mkhtml_nrm.php?e=6&k=0&m=9&n=41923&r=0&s=1&y=2025
   - The simulator scales each synthetic month’s total rainfall to the cited monthly precipitation normal.

9. **Residential waste generation varies with income and household characteristics.**
   - Afroz, Hanaki & Tudin (2011), *Environmental Monitoring and Assessment*, DOI 10.1007/s10661-010-1753-4: household size and income significantly affect waste generation.
   - https://pubmed.ncbi.nlm.nih.gov/21046234/
   - A Bangladesh planning/urban source reports DCC per-capita rates by income class (approximately 0.270 to 0.504 kg/person/day), which are used as residential calibration anchors.
   - https://www.bip.org.bd/admin/uploads/member-publication/2023/MP--7e91f817f2.pdf

10. **Dhaka’s municipal waste stream is strongly organic.**
    - A recent Dhaka life-cycle study reports organic/biowaste as the largest component (62.24% in its baseline inventory).
    - https://pmc.ncbi.nlm.nih.gov/articles/PMC12541063/
    - The generated V4.0 residual stream has an internally validated organic-family mass share of about 66.7% (organic food + fish/meat + animal residue + green/other).

11. **Seasonal differences in Dhaka MSW are not necessarily large overall; food waste is more seasonally variable.**
    - Monitoring quantity and characteristics of municipal solid waste in Dhaka City.
    - https://pubmed.ncbi.nlm.nih.gov/17503211/
    - Therefore V4.0 applies only small global seasonal multipliers and places stronger seasonality in weather, food/context, and events.

12. **Informal recycling is structurally important in Dhaka.**
    - Matter, Dietschi & Zurbrügg (2013), *Habitat International*, DOI 10.1016/j.habitatint.2012.06.001.
    - https://www.sciencedirect.com/science/article/pii/S0197397512000276
    - This supports the explicit `informal_recovery_kg` stage before residual waste enters the synthetic bin.

13. **Garment textile waste ('jhut') is actively recovered/reused in Bangladesh.**
    - BRAC University/CBS research brief, May 2025.
    - https://ced.bracu.ac.bd/wp-content/uploads/2025/06/Rumi-Akter-Jhut-Pathways-of-the-garment-and-Textile-Recycling-Industry-in-Bangladesh.pdf
    - The simulator therefore uses textile-dominant garment composition and a higher recovery parameter for garment contexts.

14. **Fish-market waste is a distinct Dhaka waste stream.**
    - A 2024 study sampled fish waste from Palashi Bazar, Hatirpool and Jatrabari fish markets in Dhaka (DOI 10.58985/jafsb.2024.v02i02.47).
    - https://www.researchgate.net/publication/380272578_Biochemical_composition_of_fish_wastes_Potentiality_for_formulation_of_cost-effective_fish_feed_for_sustainable_aquaculture
    - The simulator uses a fish/meat-dominant residual composition for Fish Market bins.

15. **Narrow/slum roads can reduce collection access and frequency.**
    - Jahan et al. (2026), PLOS ONE, DOI 10.1371/journal.pone.0346265, reports better service on wider/commercial roads and restricted access/frequency in narrow roads and slum areas.
    - https://doi.org/10.1371/journal.pone.0346265
    - V4.0 therefore models road accessibility, service level and collection delay separately from per-capita generation.

16. **Eid-ul-Adha creates an exceptional sacrificial-animal waste pulse in Dhaka.**
    - Dhaka’s two city corporations reported clearing 52,125 tonnes of sacrificial waste over three days in 2025.
    - https://www.tbsnews.net/bangladesh/dhakas-eid-waste-cleanup-mostly-satisfactory-some-hiccups-1162986
    - The dataset uses this as qualitative evidence for a strong, short-lived animal-residue and generation pulse. The simulator is not scaled to reproduce the full city tonnage.

## Scenario assumptions (not direct measurements)

The following are deliberately **not** presented as field-measured coefficients: exact hourly activity multipliers, exact Friday-prayer multiplier range, bin catchment size, synthetic bin volume, collection probabilities, sensor noise, packet-loss/anomaly probabilities, informal recovery rate ranges, Eid generation multipliers, and source-specific fine-grained composition probabilities.

These assumptions are fixed in `generate_v4_0.py`, seeded, documented, and validated so that users can reproduce or modify them.
