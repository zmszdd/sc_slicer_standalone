; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca58616e0_index_gap_grows () Bool)
(declare-fun ca58616e0_retroactive_claim_occurred () Bool)
(declare-fun ca58616e0_revived_without_reset () Bool)
(declare-fun ca58616e0_supply_index_frozen () Bool)
(assert
 (= ca58616e0_index_gap_grows ca58616e0_index_gap_grows))
(assert
 (= ca58616e0_retroactive_claim_occurred ca58616e0_retroactive_claim_occurred))
(assert
 (= ca58616e0_revived_without_reset ca58616e0_revived_without_reset))
(assert
 (= ca58616e0_supply_index_frozen ca58616e0_supply_index_frozen))
(define-fun report_preconditions () Bool (and ca58616e0_supply_index_frozen
     ca58616e0_index_gap_grows
     ca58616e0_revived_without_reset))
(define-fun report_safety () Bool (=> (and ca58616e0_supply_index_frozen
         ca58616e0_index_gap_grows
         ca58616e0_revived_without_reset)
    (not ca58616e0_retroactive_claim_occurred)))
(define-fun report_effects () Bool (and ca58616e0_supply_index_frozen
     ca58616e0_index_gap_grows
     ca58616e0_revived_without_reset
     (not (not ca58616e0_retroactive_claim_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
