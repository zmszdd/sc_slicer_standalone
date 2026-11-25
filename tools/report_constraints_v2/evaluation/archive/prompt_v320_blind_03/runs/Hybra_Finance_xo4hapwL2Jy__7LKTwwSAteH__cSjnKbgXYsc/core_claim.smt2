; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun total_weight_zero () Bool)
(declare-fun no_votes_cast () Bool)
(declare-fun ratio_zero () Bool)
(declare-fun claimable_unchanged () Bool)
(declare-fun emissions_stranded () Bool)
(assert
 (= total_weight_zero total_weight_zero))
(assert
 (= no_votes_cast no_votes_cast))
(assert
 (= ratio_zero ratio_zero))
(assert
 (= claimable_unchanged claimable_unchanged))
(assert
 (= emissions_stranded emissions_stranded))
(define-fun report_preconditions () Bool (and total_weight_zero no_votes_cast ratio_zero claimable_unchanged))
(define-fun report_safety () Bool (=> (and total_weight_zero no_votes_cast ratio_zero claimable_unchanged)
    (not emissions_stranded)))
(define-fun report_effects () Bool (and total_weight_zero
     no_votes_cast
     ratio_zero
     claimable_unchanged
     (not (not emissions_stranded))))
