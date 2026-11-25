; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c30cd904c_bonus_applied_count () Int)
(declare-fun c30cd904c_governance_manipulation_occurred () Bool)
(declare-fun c30cd904c_position_is_previously_bonused () Bool)
(assert
 (= c30cd904c_bonus_applied_count c30cd904c_bonus_applied_count))
(assert
 (= c30cd904c_governance_manipulation_occurred c30cd904c_governance_manipulation_occurred))
(assert
 (= c30cd904c_position_is_previously_bonused c30cd904c_position_is_previously_bonused))
(define-fun report_preconditions () Bool c30cd904c_position_is_previously_bonused)
(define-fun report_safety () Bool (=> c30cd904c_position_is_previously_bonused
    (>= 1 c30cd904c_bonus_applied_count)))
(define-fun report_effects () Bool (and c30cd904c_position_is_previously_bonused
     (not (>= 1 c30cd904c_bonus_applied_count))
     c30cd904c_governance_manipulation_occurred))
(assert report_preconditions)
(check-sat)
(get-model)
