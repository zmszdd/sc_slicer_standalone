; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c177e4b1a_index_delta_tokens_stranded () Bool)
(declare-fun c177e4b1a_pool_live_weight_is_zero () Bool)
(declare-fun c177e4b1a_total_weight_is_zero () Bool)
(assert
 (= c177e4b1a_index_delta_tokens_stranded c177e4b1a_index_delta_tokens_stranded))
(assert
 (= c177e4b1a_pool_live_weight_is_zero c177e4b1a_pool_live_weight_is_zero))
(assert
 (= c177e4b1a_total_weight_is_zero c177e4b1a_total_weight_is_zero))
(define-fun report_preconditions () Bool (and c177e4b1a_total_weight_is_zero c177e4b1a_pool_live_weight_is_zero))
(define-fun report_safety () Bool (=> (and c177e4b1a_total_weight_is_zero c177e4b1a_pool_live_weight_is_zero)
    (not c177e4b1a_index_delta_tokens_stranded)))
(define-fun report_effects () Bool (and c177e4b1a_total_weight_is_zero
     c177e4b1a_pool_live_weight_is_zero
     (not (not c177e4b1a_index_delta_tokens_stranded))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
