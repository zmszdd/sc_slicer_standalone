; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5dad73a1_bonus_recalculated_on_split () Bool)
(declare-fun c5dad73a1_is_smnft_lock () Bool)
(declare-fun c5dad73a1_original_amount_includes_bonus () Bool)
(declare-fun c5dad73a1_original_locked_amount () Int)
(declare-fun c5dad73a1_split_amount () Int)
(declare-fun c5dad73a1_split_fraction_denominator () Int)
(declare-fun c5dad73a1_split_fraction_numerator () Int)
(assert
 (= c5dad73a1_bonus_recalculated_on_split c5dad73a1_bonus_recalculated_on_split))
(assert
 (= c5dad73a1_is_smnft_lock c5dad73a1_is_smnft_lock))
(assert
 (= c5dad73a1_original_amount_includes_bonus c5dad73a1_original_amount_includes_bonus))
(assert
 (= c5dad73a1_original_locked_amount c5dad73a1_original_locked_amount))
(assert
 (= c5dad73a1_split_amount c5dad73a1_split_amount))
(assert
 (= c5dad73a1_split_fraction_denominator c5dad73a1_split_fraction_denominator))
(assert
 (= c5dad73a1_split_fraction_numerator c5dad73a1_split_fraction_numerator))
(define-fun report_preconditions () Bool (and c5dad73a1_is_smnft_lock c5dad73a1_original_amount_includes_bonus))
(define-fun report_safety () Bool (=> c5dad73a1_is_smnft_lock
    (= (* c5dad73a1_split_amount c5dad73a1_split_fraction_denominator)
       (* c5dad73a1_original_locked_amount c5dad73a1_split_fraction_numerator))))
(define-fun report_effects () Bool (and c5dad73a1_is_smnft_lock
     (not (= (* c5dad73a1_split_amount c5dad73a1_split_fraction_denominator)
             (* c5dad73a1_original_locked_amount
                c5dad73a1_split_fraction_numerator)))
     c5dad73a1_bonus_recalculated_on_split
     c5dad73a1_bonus_recalculated_on_split))
(assert report_preconditions)
(check-sat)
(get-model)
