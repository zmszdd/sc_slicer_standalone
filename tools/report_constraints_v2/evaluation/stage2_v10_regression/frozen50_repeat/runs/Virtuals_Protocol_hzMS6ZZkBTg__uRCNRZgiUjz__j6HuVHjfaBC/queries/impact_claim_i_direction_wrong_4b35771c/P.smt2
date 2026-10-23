; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e556fd4_elo_a_delta_direction_correct () Bool)
(declare-fun c3e556fd4_elo_b_delta_direction_correct () Bool)
(declare-fun c3e556fd4_negative () Bool)
(assert
 (= c3e556fd4_elo_a_delta_direction_correct c3e556fd4_elo_a_delta_direction_correct))
(assert
 (= c3e556fd4_elo_b_delta_direction_correct c3e556fd4_elo_b_delta_direction_correct))
(assert
 (= c3e556fd4_negative c3e556fd4_negative))
(define-fun report_preconditions () Bool (and c3e556fd4_negative (not c3e556fd4_negative)))
(define-fun report_safety () Bool (=> (or c3e556fd4_negative (not c3e556fd4_negative))
    (and c3e556fd4_elo_a_delta_direction_correct
         c3e556fd4_elo_b_delta_direction_correct)))
(define-fun report_effects () Bool (and (or c3e556fd4_negative (not c3e556fd4_negative))
     (not (and c3e556fd4_elo_a_delta_direction_correct
               c3e556fd4_elo_b_delta_direction_correct))))
(assert report_preconditions)
(check-sat)
