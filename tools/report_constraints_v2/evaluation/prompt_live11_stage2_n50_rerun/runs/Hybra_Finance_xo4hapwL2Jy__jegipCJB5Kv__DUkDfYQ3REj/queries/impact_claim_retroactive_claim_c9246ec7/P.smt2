; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca58616e0_gauge_is_killed () Bool)
(declare-fun ca58616e0_gauge_is_revived () Bool)
(declare-fun ca58616e0_index_gap_grows () Bool)
(declare-fun ca58616e0_retroactive_claim_occurs () Bool)
(declare-fun ca58616e0_supply_index_frozen_at_prekill () Bool)
(assert
 (= ca58616e0_gauge_is_killed ca58616e0_gauge_is_killed))
(assert
 (= ca58616e0_gauge_is_revived ca58616e0_gauge_is_revived))
(assert
 (= ca58616e0_index_gap_grows ca58616e0_index_gap_grows))
(assert
 (= ca58616e0_retroactive_claim_occurs ca58616e0_retroactive_claim_occurs))
(assert
 (= ca58616e0_supply_index_frozen_at_prekill ca58616e0_supply_index_frozen_at_prekill))
(define-fun report_preconditions () Bool (and ca58616e0_gauge_is_killed
     ca58616e0_supply_index_frozen_at_prekill
     ca58616e0_index_gap_grows
     ca58616e0_gauge_is_revived))
(define-fun report_safety () Bool (=> (and ca58616e0_gauge_is_killed
         ca58616e0_supply_index_frozen_at_prekill
         ca58616e0_index_gap_grows
         ca58616e0_gauge_is_revived)
    (not ca58616e0_retroactive_claim_occurs)))
(define-fun report_effects () Bool (and ca58616e0_gauge_is_killed
     ca58616e0_supply_index_frozen_at_prekill
     ca58616e0_index_gap_grows
     ca58616e0_gauge_is_revived
     (not (not ca58616e0_retroactive_claim_occurs))))
(assert report_preconditions)
(check-sat)
(get-model)
