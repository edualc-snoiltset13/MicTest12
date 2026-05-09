package com.abc_bank.abc_bank.accounts.dtos;


import com.abc_bank.abc_bank.auth_users.dtos.UserDTO;
import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.enums.AccountStatus;
import com.abc_bank.abc_bank.enums.AccountType;
import com.abc_bank.abc_bank.enums.Currency;
import com.abc_bank.abc_bank.transaction.dtos.TransactionDTO;
import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;


@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown =true)
@AllArgsConstructor
@NoArgsConstructor
public class AccountDTO {

    private Long id;

    private String accountNumber;

    private BigDecimal BALANCE=BigDecimal.ZERO;
    private AccountType accountType;

    @JsonBackReference
    private UserDTO user;

    private Currency currency;

    private AccountStatus status;

    @JsonManagedReference
    private List<TransactionDTO> transactions=new ArrayList<>();


    private LocalDateTime closedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
