; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c42dbd114_bonus_applied_count () Int)
(declare-fun c42dbd114_disproportionate_voting_power_obtained () Bool)
(declare-fun c42dbd114_one_time_bonus_count () Int)
(declare-fun c42dbd114_position_is_previously_bonused () Bool)
(assert
 (= c42dbd114_bonus_applied_count c42dbd114_bonus_applied_count))
(assert
 (= c42dbd114_disproportionate_voting_power_obtained c42dbd114_disproportionate_voting_power_obtained))
(assert
 (= c42dbd114_one_time_bonus_count c42dbd114_one_time_bonus_count))
(assert
 (= c42dbd114_position_is_previously_bonused c42dbd114_position_is_previously_bonused))
(define-fun report_preconditions () Bool c42dbd114_position_is_previously_bonused)
(define-fun report_safety () Bool (=> c42dbd114_position_is_previously_bonused
    (= c42dbd114_bonus_applied_count c42dbd114_one_time_bonus_count)))
(define-fun report_effects () Bool (and c42dbd114_position_is_previously_bonused
     (not (= c42dbd114_bonus_applied_count c42dbd114_one_time_bonus_count))
     c42dbd114_disproportionate_voting_power_obtained))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
